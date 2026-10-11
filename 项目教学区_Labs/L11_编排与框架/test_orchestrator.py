"""L11 验收：图跑通多步、人工暂停、checkpoint 恢复、幂等。"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from orchestrator import Graph, Node, GraphState, END
from loop import build_graph, _side_effects


def _pass_critic(g):
    """把 critic 改为"通过"，绕过人工，便于测试纯线性跑通。"""
    g.nodes["critic"].run = lambda d: (d.update(critic_ok=True),
                                       d.__setitem__("__next__", END))


def test_graph_runs_through_nodes():
    g = build_graph()
    _pass_critic(g)
    state, status = g.run()
    assert status == "DONE"
    assert state.done == ["planner", "executor", "critic"]


def test_human_in_the_loop_pauses():
    g = build_graph()                      # critic 默认判需人工
    state, status = g.run()
    assert status == "PAUSED_FOR_HUMAN"
    assert state.data.get("__need_human__") == "human_approve"


def test_checkpoint_resume():
    g = build_graph()
    cp = os.path.join(_HERE, "_cp_test.json")
    if os.path.exists(cp):
        os.remove(cp)
    state, status = g.run(checkpoint=cp)
    assert status == "PAUSED_FOR_HUMAN"
    state2, status2 = g.run(state=state, checkpoint=cp,
                            human_input={"__human_approved__": True})
    assert status2 == "DONE"
    assert state2.data.get("approved") is True
    assert state2.done == ["planner", "executor", "critic", "human_approve"]


def test_idempotent_no_repeat_side_effect():
    g = build_graph()
    _pass_critic(g)
    st = GraphState(data={"plan": ["a"]}, current="planner",
                    done=["planner", "executor"])   # 这两个已执行
    before = _side_effects["executor_runs"]
    state, status = g.run(state=st)
    assert status == "DONE"
    assert _side_effects["executor_runs"] == before   # executor 不重跑
