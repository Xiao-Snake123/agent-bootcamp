"""L09 演示：远端 weather 工具经 MCP bridge 接入 Agent 的 ToolRegistry（离线，无需 Key）。

运行：
    cd 项目教学区_Labs/L09_工具与外部集成
    python loop.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_core.llm import MockLLMClient
from agent_core.agent import Agent
from agent_core.tools import ToolRegistry
from mcp_server import build_demo_server
from mcp_bridge import MCPBridge


class MCPMock(MockLLMClient):
    def complete(self, messages, **kwargs):
        user = next((m["content"] for m in messages if m.get("role") == "user"), "")
        obs = [m["content"] for m in messages if m.get("role") == "tool"]
        if obs:
            return '{"final_answer": "据工具：' + obs[-1] + '"}'
        if "天气" in user:
            city = user.replace("天气", "").strip()
            return '{"action": "weather", "args": {"city": "' + city + '"}}'
        return '{"final_answer": "(Mock) ' + user + '"}'


def demo():
    print("=== MCP 接入：远端 weather 工具经 bridge 进 Agent ===")
    srv = build_demo_server()
    bridge = MCPBridge(srv)
    bridge.connect()
    reg = ToolRegistry()
    bridge.register_into(reg)
    print("  已注册工具:", [t.name for t in reg.list()])

    agent = Agent(llm=MCPMock(), tools=reg)
    final, _ = agent.run("北京天气", max_steps=4)
    print("  最终:", final)
    print("  → 远端工具与本地工具一样落在 ToolRegistry，Agent 主循环无感调用。")


if __name__ == "__main__":
    demo()
