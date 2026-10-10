"""L03 pytest 验收测试。运行：pytest test_fc.py"""

import os
import sys
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_core.tools import ToolRegistry
from tools_fc import WeatherTool, CalculatorTool
from fc import tools_to_openai_schema, FunctionCallingAgent
from mock_fc import MockFunctionCaller


def _build():
    reg = ToolRegistry()
    reg.register(WeatherTool())
    reg.register(CalculatorTool())
    return FunctionCallingAgent(llm=MockFunctionCaller(), tools=reg), reg


def test_schema_conversion():
    """验收：工具能被正确转成 OpenAI function-calling 格式。"""
    reg = ToolRegistry()
    reg.register(WeatherTool())
    sch = tools_to_openai_schema(reg)
    assert sch[0]["type"] == "function"
    assert sch[0]["function"]["name"] == "get_weather"
    assert "city" in sch[0]["function"]["parameters"]["properties"]


def test_single_tool_dispatch():
    """验收：单工具调用被正确分发并回收观察。"""
    agent, _ = _build()
    final, traj = agent.run("北京天气怎么样")
    assert traj[0]["action"]["name"] == "get_weather"
    assert "晴" in traj[0]["observation"]


def test_parallel_calls():
    """验收：一句目标触发多个并行 tool_calls。"""
    agent, _ = _build()
    final, traj = agent.run("帮我算 23 * 17 并查上海天气")
    names = [s["action"]["name"] for s in traj if s["action"]]
    assert "calculator" in names and "get_weather" in names


def test_param_validation_clean():
    """验收：工具对不合规参数返回 ok=False（dispatch 前已清洗/拒绝）。"""
    reg = ToolRegistry()
    reg.register(CalculatorTool())
    obs = reg.dispatch("calculator", {"expr": "import os"})
    assert obs.ok is False


def test_unknown_tool_rejected():
    """验收：模型返回未知工具名时，Agent 拒绝执行而非崩溃。"""

    class BadMock(MockFunctionCaller):
        def complete(self, messages, tools=None, **kwargs):
            return json.dumps({"thought": "x",
                               "tool_calls": [{"name": "nope", "arguments": {}}]},
                              ensure_ascii=False)

    agent, _ = _build()
    agent.llm = BadMock()
    final, traj = agent.run("随便做点什么")
    assert traj[0]["observation"] == "未知工具：nope"
