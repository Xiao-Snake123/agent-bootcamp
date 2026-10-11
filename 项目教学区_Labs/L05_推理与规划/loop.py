"""L05 演示：Plan-and-Execute vs ReAct（离线，无需 Key）。

运行：
    cd 项目教学区_Labs/L05_推理与规划
    python loop.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_core.llm import MockLLMClient
from agent_core.agent import Agent
from planner import MockPlanner
from executor import PlanExecutor


def demo_plan_and_execute():
    print("=== Plan-and-Execute（先规划，再逐步执行）===")
    planner = MockPlanner()
    plan = planner.plan("查天气并建议穿衣")
    print("计划:", plan)
    ex = PlanExecutor(step_fn=lambda s: f"[执行] {s} -> 完成")
    results = ex.run(plan)
    for s, r in zip(plan, results):
        print(f"  步骤: {s}\n    结果: {r}")


def demo_react():
    print("\n=== ReAct（边想边做，对照）===")
    agent = Agent(llm=MockLLMClient(), tools=None)
    final, traj = agent.run("查天气并建议穿衣", max_steps=3)
    print("  ReAct 最终:", final)
    print("  （无预规划，单 loop 内 思考→动作→观察 交织）")


if __name__ == "__main__":
    demo_plan_and_execute()
    demo_react()
