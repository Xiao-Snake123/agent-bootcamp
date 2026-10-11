"""L07 验收：三角色产出非空 + 编排者跑通评审循环并收敛。"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from message_bus import MessageBus
from roles import Researcher, Writer, Critic
from orchestrator import Orchestrator


def test_roles_produce():
    bus = MessageBus()
    bus.topic = "X"
    assert Researcher().act(bus)
    assert Writer().act(bus)
    assert Critic().act(bus)


def test_orchestrator_produces_reviewed_doc():
    bus = MessageBus()
    orch = Orchestrator(bus, max_rounds=3)
    hist = orch.run("Agent 教学")
    roles = [r for r, _ in hist]
    assert "Researcher" in roles and "Writer" in roles and "Critic" in roles
    assert any("通过" in c for _, c in hist)


def test_review_loop_converges():
    bus = MessageBus()
    orch = Orchestrator(bus, max_rounds=3)
    orch.run("X")
    writer_count = sum(1 for r, _ in bus.history if r == "Writer")
    assert writer_count == 2   # 初稿 1 次 + 评审要求修改后重修 1 次
