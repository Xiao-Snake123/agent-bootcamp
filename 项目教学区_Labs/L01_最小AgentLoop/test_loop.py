"""L01 pytest 验收测试。运行：pytest test_loop.py"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_core.agent import Agent
from agent_core.llm import MockLLMClient
from agent_core.tools import ToolRegistry
from tools_basic import CalculatorTool


def _build_agent():
    reg = ToolRegistry()
    reg.register(CalculatorTool())
    return Agent(llm=MockLLMClient(), tools=reg)


def test_agent_loop_terminates_with_trajectory():
    """验收：给定目标能自主循环 ≤N 步并终止，轨迹可读（含 Thought/Action/Observation）。"""
    agent = _build_agent()
    answer, traj = agent.run("帮我算 23 * 17 是多少", max_steps=5)

    assert traj.final_answer
    assert traj.final_answer != "（达到步数上限，未给出最终答案）"
    assert len(traj.steps) >= 1

    actions = [s for s in traj.steps if s.action]
    assert actions, "轨迹中应包含至少一次 Action"
    assert actions[0].action["name"] == "calculator"
    assert actions[0].observation and actions[0].observation != "（终止）"


def test_unknown_tool_does_not_crash():
    """未知工具应返回 ok=False 的观察（含"未知工具"），而不是让循环崩溃。"""

    class UnknownToolMock(MockLLMClient):
        def complete(self, messages, **kwargs):
            return '{"thought": "故意调一个不存在的工具", "action": "nonexistent", "args": {}}'

    reg = ToolRegistry()
    reg.register(CalculatorTool())
    agent = Agent(llm=UnknownToolMock(), tools=reg)
    answer, traj = agent.run("随便做点什么", max_steps=3)

    assert isinstance(answer, str)  # 不抛异常，循环可继续/正常结束
    unknown_steps = [s for s in traj.steps if s.action.get("name") == "nonexistent"]
    assert unknown_steps, "应触发未知工具分支"
    assert "未知工具" in unknown_steps[0].observation


def test_max_steps_cap():
    """步数上限生效：永不终止的决策者应在 max_steps 后停止。"""

    class LoopMock(MockLLMClient):
        def complete(self, messages, **kwargs):
            return '{"action": "calculator", "args": {"expr": "1+1"}}'

    reg = ToolRegistry()
    reg.register(CalculatorTool())
    agent = Agent(llm=LoopMock(), tools=reg)
    answer, traj = agent.run("一直循环", max_steps=3)

    assert len(traj.steps) <= 3
    assert "达到步数上限" in traj.final_answer
