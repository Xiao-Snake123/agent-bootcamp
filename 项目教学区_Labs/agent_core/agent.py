"""最小 Agent Loop + 轨迹记录（K1 核心）。"""

import json
from dataclasses import dataclass, field

from .tools import Observation


@dataclass
class Step:
    """轨迹中的一步：一次思考 + 可能的一次动作 + 一次观察。"""
    thought: str = ""
    action: dict = field(default_factory=dict)   # {"name":..., "args":...}
    observation: str = ""


@dataclass
class Trajectory:
    """整轮运行的轨迹，供 K11 评估/回放复用。"""
    steps: list = field(default_factory=list)
    final_answer: str = ""


class Agent:
    def __init__(self, llm, tools=None, memory=None):
        self.llm = llm
        self.tools = tools   # ToolRegistry 或 None
        self.memory = memory # Memory 或 None（K4 启用）

    def run(self, goal: str, max_steps: int = 10):
        """最小闭环：思考→动作→观察→再思考→终止。返回 (最终答案, Trajectory)。"""
        messages = [{"role": "user", "content": goal}]
        traj = Trajectory()
        for _ in range(max_steps):
            raw = self.llm.complete(messages)
            decision = self._parse(raw)
            if "final_answer" in decision:
                traj.final_answer = decision["final_answer"]
                traj.steps.append(Step(thought=raw, observation="（终止）"))
                break
            name = decision.get("action")
            args = decision.get("args", {}) or {}
            step = Step(thought=raw, action={"name": name, "args": args})
            if self.tools is None or name not in [t.name for t in self.tools.list()]:
                obs = Observation(content=f"未知工具：{name}", ok=False)
            else:
                obs = self.tools.dispatch(name, args)
            step.observation = obs.content
            traj.steps.append(step)
            messages.append({"role": "tool", "content": obs.content})
            if self.memory:
                self.memory.add(step)
        else:
            traj.final_answer = "（达到步数上限，未给出最终答案）"
        return traj.final_answer, traj

    @staticmethod
    def _parse(raw: str) -> dict:
        """把模型输出解析为决策。L1 用简化 JSON 协议；K3 会升级为真正的 Function Calling。"""
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {"final_answer": raw.strip()}
