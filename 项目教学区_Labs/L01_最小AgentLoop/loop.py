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


if __name__ == "__main__":
    main()
