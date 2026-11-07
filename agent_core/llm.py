"""LLM 统一接口层（v2 重生版）。

修掉 v1 的三个致命问题：
1. ``complete() -> str`` 丢弃 ``tool_calls`` → 新增 ``chat()`` 返回 ChatResponse（含 ToolCall）。
2. Agent 手写 ``{action, args}`` JSON 协议 → 改走原生 Function Calling。
3. ``unit_price=0.0`` 使成本护栏永不触发 → 改为可配置真实单价（元/百万 token）。

保留 v1 的 LLMClient / Usage / CostLimitError / complete() 接口形状，旧代码可平滑迁移。
"""
from __future__ import annotations

import json
import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class CostLimitError(Exception):
    """累计成本超过 max_cost（元）时抛出，防止 demo 真跑烧钱。"""


@dataclass
class Usage:
    """一次客户端生命周期内的累计用量。"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class ToolCall:
    """一条模型发起的工具调用（OpenAI/DeepSeek 兼容结构）。"""
    id: str
    name: str
    arguments: dict = field(default_factory=dict)


@dataclass
class ChatResponse:
    """chat() 的统一返回：文本 + 工具调用 + 可直接回注的 assistant 消息。"""
    content: str = ""
    tool_calls: list = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    message: dict = field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)


def _assistant_message(content: str, tool_calls: list) -> dict:
    """构造严格符合 OpenAI/DeepSeek 协议的 assistant 消息。"""
    msg = {"role": "assistant", "content": content or ""}
    if tool_calls:
        msg["tool_calls"] = [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.name,
                          "arguments": json.dumps(tc.arguments, ensure_ascii=False)}}
            for tc in tool_calls
        ]
    return msg


class LLMClient(ABC):
    """所有后端的统一接口：chat() 为主，complete() 为兼容便捷接口。"""

    def __init__(self, model: str = "", max_cost: float = 0.30,
                 price_in: float = 2.0, price_out: float = 8.0):
        self.model = model
        self.max_cost = max_cost
        # 单价：元 / 百万 token，仅作护栏估算，真实计费以账单为准
        self.price_in = price_in
        self.price_out = price_out
        self.usage = Usage()

    @abstractmethod
    def chat(self, messages: list, tools: list | None = None,
             tool_choice: str = "auto", **kwargs) -> ChatResponse:
        """给定消息（可带 tools schema），返回完整响应（含 tool_calls）。"""

    def complete(self, messages: list, **kwargs) -> str:
        """v1 兼容接口：只要文本。"""
        return self.chat(messages, **kwargs).content

    def _check_budget(self):
        if self.usage.cost >= self.max_cost:
            raise CostLimitError(
                f"预算已用尽：累计 {self.usage.cost:.4f} 元 / 上限 {self.max_cost} 元")

    def _accrue(self, prompt_tokens: int, completion_tokens: int):
        self.usage.prompt_tokens += prompt_tokens
        self.usage.completion_tokens += completion_tokens
        self.usage.calls += 1
        self.usage.cost += (prompt_tokens * self.price_in
                            + completion_tokens * self.price_out) / 1_000_000
        if self.usage.cost > self.max_cost:
            raise CostLimitError(
                f"累计成本 {self.usage.cost:.4f} 元已超过上限 {self.max_cost} 元")


class OpenAICompatibleClient(LLMClient):
    """OpenAI 兼容云端后端（DeepSeek / DashScope / OpenAI / 自建网关通用）。"""

    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(model=model, **kwargs)
        from openai import OpenAI  # 延迟导入：无 SDK 时 Mock 仍可用
        self.base_url = base_url
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=30.0)

    def chat(self, messages: list, tools: list | None = None,
             tool_choice: str = "auto", **kwargs) -> ChatResponse:
        self._check_budget()
        params = {"model": self.model, "messages": messages, **kwargs}
        if tools:  # 空 tools 会让部分网关报错，故仅在非空时传
            params["tools"] = tools
            params["tool_choice"] = tool_choice
        resp = self._client.chat.completions.create(**params)
        msg = resp.choices[0].message

        calls = []
        for tc in (msg.tool_calls or []):
            try:
                args = json.loads(tc.function.arguments or "{}")
            except (json.JSONDecodeError, TypeError):
                args = {}
            calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))

        u = getattr(resp, "usage", None)
        self._accrue(getattr(u, "prompt_tokens", 0) or 0,
                     getattr(u, "completion_tokens", 0) or 0)
        return ChatResponse(
            content=msg.content or "", tool_calls=calls, usage=self.usage,
            message=_assistant_message(msg.content or "", calls))


def tool_call(name: str, **arguments) -> dict:
    """供 MockLLMClient 脚本使用的工具调用声明。"""
    return {"tool_calls": [{"name": name, "arguments": arguments}]}


class MockLLMClient(LLMClient):
    """离线决策器：不联网、不需要 Key，但完整模拟原生 Function Calling 协议。

    - 可用 ``script`` 注入逐轮响应（字符串 / dict / ChatResponse），跑通任意 demo 的链路；
    - 脚本耗尽后按规则兜底：已有 tool 结果 → 给结论；目标含算式且有 calculator → 调工具。
    """

    def __init__(self, script: list | None = None, **kwargs):
        kwargs.setdefault("max_cost", 0.30)
        super().__init__(model="mock", **kwargs)
        self._script = list(script or [])

    def _scripted(self, item) -> ChatResponse | None:
        if isinstance(item, ChatResponse):
            item.usage = self.usage
            return item
        if isinstance(item, str):
            content = item
            spec = {}
        elif isinstance(item, dict):
            content = item.get("content", "")
            spec = item
        else:
            return None
        calls = [ToolCall(id=f"call_{uuid.uuid4().hex[:8]}",
                          name=c["name"], arguments=c.get("arguments", {}))
                 for c in spec.get("tool_calls", [])]
        return ChatResponse(content=content, tool_calls=calls, usage=self.usage,
                            message=_assistant_message(content, calls))

    def chat(self, messages: list, tools: list | None = None,
             tool_choice: str = "auto", **kwargs) -> ChatResponse:
        self._check_budget()
        goal = next((m.get("content", "") for m in messages
                     if m.get("role") == "user"), "")
        observations = [m.get("content", "") for m in messages
                        if m.get("role") == "tool"]
        known = {t["function"]["name"] for t in (tools or [])
                 if t.get("type") == "function"}

        result = None
        while self._script:
            result = self._scripted(self._script.pop(0))
            if result is not None:
                break
        if result is None:
            content, calls = "", []
            if observations:
                content = f"根据工具结果，结论是：{observations[-1]}"
            else:
                m = re.search(r"(\d+)\s*([\*\+\-/])\s*(\d+)", str(goal))
                if m and "calculator" in known:
                    calls = [ToolCall(id=f"call_{uuid.uuid4().hex[:8]}",
                                      name="calculator",
                                      arguments={"expr": f"{m.group(1)}{m.group(2)}{m.group(3)}"})]
                else:
                    content = f"（离线 Mock）已理解目标：{goal}"
            result = ChatResponse(content=content, tool_calls=calls, usage=self.usage,
                                  message=_assistant_message(content, calls))

        self._accrue(len(str(goal)) // 4 + 8, 16)
        return result
