"""L01 演示入口：跑通最小 Agent Loop 并打印轨迹。

运行（无需 API Key，默认用 MockLLMClient）：
    cd 项目教学区_Labs/L01_最小AgentLoop
    python loop.py
"""

import os
import sys

# 让本脚本既能直接运行，也能被 pytest 导入：把 agent_core 与当前目录加入路径
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_core.agent import Agent
from agent_core.llm import MockLLMClient
from agent_core.tools import ToolRegistry
from tools_basic import CalculatorTool


def main():
    reg = ToolRegistry()
    reg.register(CalculatorTool())

    llm = MockLLMClient()           # 离线决策器，不联网
    agent = Agent(llm=llm, tools=reg)

    goal = "帮我算 23 * 17 是多少"
    answer, traj = agent.run(goal, max_steps=5)

    print("目标:", goal)
    print("最终答案:", answer)
    print("\n--- 轨迹（Thought / Action / Observation）---")
    for i, s in enumerate(traj.steps, 1):
        print(f"\n步骤 {i}:")
        print("  Thought   :", s.thought)
        if s.action:
            print("  Action    :", s.action)
        print("  Observation:", s.observation)

    print("\nToken 用量:", llm.usage.total_tokens, "｜ 累计成本:", round(llm.usage.cost, 6))

    print("\n" + "=" * 40)
    demo_multi_step()


def demo_multi_step():
    """多步循环演示：展示 Agent 不止一次函数调用，而是反复决策—执行—回收。"""
    reg = ToolRegistry()
    reg.register(CalculatorTool())

    class TwoStepMock(MockLLMClient):
        def complete(self, messages, **kwargs):
            has_tool = any(m.get("role") == "tool" for m in messages)
            if not has_tool:
                return '{"thought": "先算边长5的正方形面积", "action": "calculator", "args": {"expr": "5*5"}}'
            return '{"thought": "已得到面积25，给出最终答案", "final_answer": "正方形面积=25"}'

    agent = Agent(llm=TwoStepMock(), tools=reg)
    goal = "帮我算一个边长5的正方形面积"
    answer, traj = agent.run(goal, max_steps=5)
    print("目标:", goal)
    print("最终答案:", answer)
    print("--- 多步轨迹 ---")
    for i, s in enumerate(traj.steps, 1):
        print(f"步骤 {i}: Thought={s.thought} Action={s.action} Observation={s.observation}")


if __name__ == "__main__":
    main()
