"""L12 验收：过程/结果评分 + 护栏拦截 + 预算截断。"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_core.agent import Agent, Trajectory, Step
from agent_core.llm import MockLLMClient
from agent_core.tools import ToolRegistry, Tool, Observation
from eval_panel import Guardrail, Budget, score_process, score_outcome


def test_guardrail_blocks_danger():
    g = Guardrail()
    ok, hits = g.check_input("帮我删除数据库")
    assert not ok and hits
    # 正常输入应通过
    ok2, _ = g.check_input("今天天气如何")
    assert ok2


def test_guardrail_blocks_leak_output():
    g = Guardrail()
    ok, hits = g.check_output("这是你的 api_key: sk-abcdefghijkl")
    assert not ok and hits


def test_result_score_low_when_no_answer():
    t = Trajectory(final_answer="（达到步数上限，未给出最终答案）")
    assert score_outcome(t, "目标") == 0.0


def test_process_score_high_when_steps_valid():
    t = Trajectory(
        steps=[
            Step(thought="想调搜索", action={"name": "search", "args": {}},
                 observation="搜索结果：x"),
            Step(thought="再总结", observation="（终止）"),
        ],
        final_answer="据搜索：已完成",
    )
    assert score_process(t) == 1.0


def test_budget_truncates():
    class TwoStepLLM(MockLLMClient):
        def complete(self, messages, **kw):
            obs = [m for m in messages if m.get("role") == "tool"]
            if obs:
                return '{"final_answer": "done"}'
            return '{"action": "t", "args": {}}'

    class T(Tool):
        name = "t"
        description = ""
        schema = {"properties": {}}

        def run(self, **k):
            return Observation(content="ok")

    agent = Agent(llm=TwoStepLLM(), tools=ToolRegistry())
    agent.tools.register(T())
    final, traj = agent.run("go", max_steps=1)   # 预算=1步，未到 final
    assert "未给出" in final
    assert score_outcome(traj, "go") == 0.0
