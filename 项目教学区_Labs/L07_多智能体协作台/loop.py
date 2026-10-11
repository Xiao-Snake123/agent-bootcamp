"""L07 演示：Researcher → Writer → Critic 三角色经 message bus 协作（离线，无需 Key）。

运行：
    cd 项目教学区_Labs/L07_多智能体协作台
    python loop.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from message_bus import MessageBus
from orchestrator import Orchestrator


def demo():
    print("=== 多智能体协作台（Researcher/Writer/Critic）===")
    bus = MessageBus()
    orch = Orchestrator(bus, max_rounds=3)
    history = orch.run("AI Agent 教学")
    for role, content in history:
        print(f"  [{role}] {content}")
    print("  → Critic 首轮要求补风险段，Writer 重修后次轮通过。")


if __name__ == "__main__":
    demo()
