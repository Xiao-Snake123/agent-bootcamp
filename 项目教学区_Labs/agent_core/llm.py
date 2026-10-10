"""LLM 客户端抽象层。

设计要点（对应 design_docs/03 §2.2 / §7）：
- LLMClient 是抽象基类，所有具体后端（OpenAI 兼容云端 / 离线 Mock）都实现 complete()。
- 内置 token 计数与成本上限，累计超过 MAX_COST 抛 CostLimitError，避免烧钱。
- P0 阶段用 MockLLMClient 即可跑通，无需任何 API Key。
- 真实后端按决策只接 OpenAI 兼容云端（见 .env.example）。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class CostLimitError(Exception):
    """累计成本超过 MAX_COST 上限时抛出。"""


@dataclass
class Usage:
    """一次客户端生命周期内的用量累计。"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class LLMClient(ABC):
    """所有 LLM 后端的统一接口。"""

    def __init__(self, model: str = "", max_cost: float = 1.0):
        self.model = model
        self.max_cost = max_cost
        self.usage = Usage()

    @abstractmethod
    def complete(self, messages: list, **kwargs) -> str:
        """给定对话消息，返回模型文本输出。"""
        ...

    def _accrue(self, prompt_tokens: int, completion_tokens: int, unit_price: float = 0.0):
        """累计用量并在超限时抛错。unit_price 单位：美元/token。"""
        self.usage.prompt_tokens += prompt_tokens
        self.usage.completion_tokens += completion_tokens
        self.usage.cost += (prompt_tokens + completion_tokens) * unit_price
        if self.usage.cost > self.max_cost:
            raise CostLimitError(
                f"累计成本 {self.usage.cost:.4f} 美元已超过上限 {self.max_cost}"
            )


class OpenAIClient(LLMClient):
    """OpenAI 兼容云端后端（本教学唯一的真实后端，需 API Key）。"""

    def __init__(self, api_key: str = "", base_url: str = "",
                 model: str = "gpt-4o-mini", max_cost: float = 1.0):
        super().__init__(model=model, max_cost=max_cost)
        from openai import OpenAI  # 延迟导入：未装 openai 也不影响 Mock/导入
        self._client = OpenAI(api_key=api_key or None, base_url=base_url or None)

    def complete(self, messages: list, **kwargs) -> str:
        resp = self._client.chat.completions.create(
            model=self.model, messages=messages, **kwargs
        )
        u = resp.usage
        # 价格仅作示例（美元/token），真实计费以账单为准
        self._accrue(u.prompt_tokens, u.completion_tokens, unit_price=0.0)
        return resp.choices[0].message.content


class MockLLMClient(LLMClient):
    """离线演示/测试用决策器：不联网、不需要 Key。

    它不是一个"真模型"，而是一个最小决策策略，用来把 Agent 的
    思考→动作→观察 循环跑通：
      - 若对话里已出现过工具结果（role=tool），说明动作已执行，直接给最终答案；
      - 否则若目标含"算"+数字运算符，产出 calculator 动作；
      - 否则直接给一个文字最终答案。
    这样 L1 无需任何 API Key 即可演示与 pytest 验收。
    """

    def complete(self, messages: list, **kwargs) -> str:
        import re
        import json

        goal = messages[0]["content"] if messages else ""
        has_observation = any(m.get("role") == "tool" for m in messages)

        if has_observation:
            obs_list = [m["content"] for m in messages if m.get("role") == "tool"]
            decision = {"final_answer": f"根据工具结果，结论是：{obs_list[-1]}"}
        elif "算" in goal and re.search(r"\d+\s*[\*\+\-\/]\s*\d+", goal):
            m = re.search(r"(\d+)\s*([\*\+\-\/])\s*(\d+)", goal)
            a, op, b = m.group(1), m.group(2), m.group(3)
            decision = {"action": "calculator", "args": {"expr": f"{a}{op}{b}"}}
        else:
            decision = {"final_answer": f"（Mock）已理解目标：{goal}"}

        # 模拟少量 token 消耗，便于演示成本护栏
        self._accrue(len(goal) // 4 + 4, 8)
        return json.dumps(decision, ensure_ascii=False)
