"""L03 演示：单工具调用 与 并行多工具调用（离线、无需 Key）。"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_core.tools import ToolRegistry
from tools_fc import WeatherTool, CalculatorTool
from fc import FunctionCallingAgent, tools_to_openai_schema
from mock_fc import MockFunctionCaller


def _print(traj, final):
    for i, s in enumerate(traj, 1):
        print(f"  步骤{i}: Thought={s['thought']}")
        if s["action"]:
            print(f"         Action ={s['action']}")
        print(f"         Obs    ={s['observation']}")
    print("  最终:", final)


def main():
    reg = ToolRegistry()
    reg.register(WeatherTool())
    reg.register(CalculatorTool())

    print("=== 工具 schema（OpenAI function-calling 格式）===")
    print(tools_to_openai_schema(reg))

    agent = FunctionCallingAgent(llm=MockFunctionCaller(), tools=reg)

    print("\n=== 单工具：查天气 ===")
    final, traj = agent.run("北京天气怎么样")
    _print(traj, final)

    print("\n=== 并行多工具：算数 + 查天气 ===")
    final, traj = agent.run("帮我算 23 * 17 并查上海天气")
    _print(traj, final)


if __name__ == "__main__":
    main()
