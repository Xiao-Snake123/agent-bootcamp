"""L03 离线 Function-Calling 决策器：根据目标返回合规 tool_calls。"""

import json
import re
from agent_core.llm import LLMClient


class MockFunctionCaller(LLMClient):
    """不联网：根据目标里的关键词挑工具，返回 OpenAI 风格的 tool_calls。

    注意：为离线演示，我们在 tool_calls 里塞了一个 `thought` 字段，并省略了
    真实 API 必带的 `id`/`tool_call_id`——Agent 会自行补 id。接入真实 API 时，
    模型不返回 `thought`，且并行调用必须带 `tool_call_id`（见 K3 陷阱⑤⑨）。
    """

    def complete(self, messages, tools=None, **kwargs):
        goal = next((m["content"] for m in messages if m.get("role") == "user"), "")
        has_obs = any(m.get("role") == "tool" for m in messages)

        if has_obs:
            last = [m["content"] for m in messages if m.get("role") == "tool"][-1]
            return json.dumps({
                "thought": f"已拿到工具结果 {last}，可给出最终答案",
                "final_answer": f"根据工具结果，结论是：{last}",
            }, ensure_ascii=False)

        calls = []
        if "天气" in goal:
            # mock 仅识别内置城市；用直接包含匹配，避免脆弱正则把前缀汉字吞进城市名
            city = next((c for c in ("北京", "上海", "广州") if c in goal), "北京")
            calls.append({"name": "get_weather", "arguments": {"city": city}})
        if "算" in goal and re.search(r"\d+\s*[\*\+\-\/]\s*\d+", goal):
            m = re.search(r"(\d+)\s*([\*\+\-\/])\s*(\d+)", goal)
            calls.append({"name": "calculator",
                          "arguments": {"expr": f"{m.group(1)}{m.group(2)}{m.group(3)}"}})
        if any(k in goal for k in ("搜", "查资料", "资料")):
            calls.append({"name": "get_search", "arguments": {"query": goal}})

        if calls:
            return json.dumps({
                "thought": f"需要调用 {len(calls)} 个工具",
                "tool_calls": calls,
            }, ensure_ascii=False)
        return json.dumps({
            "thought": "无需工具，直接回答",
            "final_answer": f"（Mock）已理解目标：{goal}",
        }, ensure_ascii=False)
