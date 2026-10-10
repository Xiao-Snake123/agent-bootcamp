"""L03 核心：工具描述→OpenAI tools 格式 + 支持 tool_calls 的 Agent。"""

import json
from agent_core.tools import ToolRegistry, Observation


def _parse(raw: str) -> dict:
    """把模型输出解析为决策 dict；解析失败则当作最终答案文本。"""
    try:
        d = json.loads(raw)
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    return {"final_answer": raw.strip()}


def tools_to_openai_schema(registry: ToolRegistry) -> list:
    """把 ToolRegistry 里的工具转成 OpenAI function-calling 的 tools 参数。"""
    out = []
    for t in registry.list():
        params = t.schema or {"type": "object", "properties": {}}
        out.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": params,
            },
        })
    return out


class FunctionCallingAgent:
    """支持 tool_calls 的最小 Agent：LLM 返回 [{name, arguments}]，逐个 dispatch。

    与 L1 的 Agent 区别：决策不再是手写 {action:...} JSON，而是模型原生的
    tool_calls 列表；一轮可含多个调用（并行）。
    """

    def __init__(self, llm, tools: ToolRegistry):
        self.llm = llm
        self.tools = tools

    def run(self, goal: str, max_steps: int = 8):
        messages = [{"role": "user", "content": goal}]
        tool_schemas = tools_to_openai_schema(self.tools)
        traj = []
        final = ""
        for _ in range(max_steps):
            decision = _parse(self.llm.complete(messages, tools=tool_schemas))
            if "final_answer" in decision:
                final = decision["final_answer"]
                traj.append({"thought": decision.get("thought", ""),
                             "action": None,
                             "observation": "（终止）"})
                break
            calls = decision.get("tool_calls", [])
            if not calls:
                final = decision.get("final_answer", str(decision))
                break
            for call in calls:
                name = call.get("name")
                args = call.get("arguments", {}) or {}
                if name not in [t.name for t in self.tools.list()]:
                    obs = Observation(content=f"未知工具：{name}", ok=False)
                else:
                    obs = self.tools.dispatch(name, args)
                traj.append({
                    "thought": decision.get("thought", ""),
                    "action": {"name": name, "args": args},
                    "observation": obs.content,
                })
                messages.append({"role": "tool", "content": obs.content, "name": name})
        else:
            final = "（达到步数上限，未给出最终答案）"
        return final, traj
