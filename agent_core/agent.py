"""Agent 主循环（v2）：原生 Function Calling 闭环。

v1 的致命问题：手写 ``{action, args}`` JSON，回注 ``role=tool`` 无 tool_call_id，
真实 DeepSeek/OpenAI API 必 400。v2 严格走标准协议：

    assistant(tool_calls=[{id,...}]) → tool(tool_call_id=id, content=...) → assistant ...

另加三道护栏：max_steps、max_cost（由 LLMClient 抛 CostLimitError）、重复调用检测。
保留 v1 的 Step / Trajectory / Agent.run(goal, max_steps) 形状，供评测模块复用。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from .llm import CostLimitError
from .tools import Observation, ToolRegistry


@dataclass
class Step:
    """轨迹中的一步：一次模型输出 + 一次工具调用 + 一次观察。"""
    thought: str = ""
    action: dict = field(default_factory=dict)   # {"name":..., "args":...}
    observation: str = ""
    ok: bool = True
    tool_call_id: str = ""


@dataclass
class Trajectory:
    """整轮轨迹，供 eval.py 评测 / 回放复用。"""
    steps: list = field(default_factory=list)
    final_answer: str = ""
    stop_reason: str = ""

    @property
    def tool_calls(self) -> list:
        return [s for s in self.steps if s.action]

    @property
    def failed_calls(self) -> list:
        return [s for s in self.steps if not s.ok]


class Agent:
    """最小但真实的 Agent：LLM + 工具 + 记忆 + 预算/循环护栏。"""

    def __init__(self, llm, tools: ToolRegistry | None = None, memory=None,
                 system: str = "", max_cost: float | None = None,
                 loop_limit: int = 3):
        self.llm = llm
        self.tools = tools or ToolRegistry()
        self.memory = memory
        self.system = system
        self.loop_limit = loop_limit
        if max_cost is not None:
            self.llm.max_cost = max_cost

    def run(self, goal: str, max_steps: int = 10):
        """返回 (final_answer, Trajectory)。"""
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})
        if self.memory is not None:
            recalled = self.memory.get(goal)
            if recalled:
                messages.append({"role": "system",
                                 "content": "相关记忆：\n" + "\n".join(map(str, recalled))})
        messages.append({"role": "user", "content": goal})

        traj = Trajectory()
        seen: dict[str, int] = {}
        schemas = self.tools.openai_schemas()

        for _ in range(max_steps):
            try:
                resp = self.llm.chat(messages, tools=schemas or None)
            except CostLimitError as e:
                traj.final_answer = f"（成本护栏触发：{e}）"
                traj.stop_reason = "cost_limit"
                break

            if not resp.has_tool_calls:
                traj.final_answer = resp.content
                traj.stop_reason = "final"
                break

            # 关键：先回注带 tool_calls 的 assistant 消息，再逐条回注 tool 结果
            messages.append(resp.message)
            for tc in resp.tool_calls:
                sig = tc.name + "|" + json.dumps(tc.arguments, sort_keys=True,
                                                 ensure_ascii=False)
                seen[sig] = seen.get(sig, 0) + 1
                if seen[sig] > self.loop_limit:
                    obs = Observation(
                        f"检测到重复调用 {tc.name} 共 {seen[sig]} 次，已强制终止以防死循环",
                        ok=False)
                    traj.stop_reason = "loop_detected"
                else:
                    obs = self.tools.dispatch(tc.name, tc.arguments)
                messages.append({"role": "tool", "tool_call_id": tc.id,
                                 "content": obs.content})
                step = Step(thought=resp.content,
                            action={"name": tc.name, "args": tc.arguments},
                            observation=obs.content, ok=obs.ok,
                            tool_call_id=tc.id)
                traj.steps.append(step)
                if self.memory is not None:
                    self.memory.add(step)
                if traj.stop_reason == "loop_detected":
                    break

            if traj.stop_reason == "loop_detected":
                traj.final_answer = f"（检测到循环，已终止）{traj.steps[-1].observation}"
                break
        else:
            traj.final_answer = "（达到步数上限，未给出最终答案）"
            traj.stop_reason = "max_steps"

        return traj.final_answer, traj
