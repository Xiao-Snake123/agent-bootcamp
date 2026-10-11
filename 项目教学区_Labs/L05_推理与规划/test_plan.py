"""L05 验收：规划拆分正确 + 执行器逐步跑完所有子目标。"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from planner import MockPlanner
from executor import PlanExecutor


def test_planner_splits_compound_goal():
    p = MockPlanner()
    plan = p.plan("查天气并建议穿衣")
    assert isinstance(plan, list) and len(plan) == 2
    assert "查天气" in plan[0]


def test_planner_default_three_steps():
    p = MockPlanner()
    plan = p.plan("写一首诗")
    assert len(plan) == 3


def test_executor_runs_all_steps():
    p = MockPlanner()
    plan = p.plan("查天气并建议穿衣")
    ex = PlanExecutor(step_fn=lambda s: f"done:{s}")
    results = ex.run(plan)
    assert len(results) == len(plan)
    assert all(r.startswith("done:") for r in results)
