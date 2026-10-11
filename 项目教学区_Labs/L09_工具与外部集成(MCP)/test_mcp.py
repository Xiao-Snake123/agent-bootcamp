"""L09 验收：server 列工具、bridge 注册、远端调用经 bridge 转发。"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_core.tools import ToolRegistry
from mcp_server import build_demo_server
from mcp_bridge import MCPBridge


def test_server_lists_tool_schema():
    srv = build_demo_server()
    schemas = srv.list_tools()
    assert any(s["name"] == "weather" for s in schemas)


def test_bridge_registers_remote_tool():
    srv = build_demo_server()
    bridge = MCPBridge(srv)
    bridge.connect()
    reg = ToolRegistry()
    bridge.register_into(reg)
    assert "weather" in [t.name for t in reg.list()]


def test_remote_tool_call_forwards():
    srv = build_demo_server()
    bridge = MCPBridge(srv)
    bridge.connect()
    reg = ToolRegistry()
    bridge.register_into(reg)
    obs = reg.dispatch("weather", {"city": "上海"})
    assert "上海" in obs.content and "晴" in obs.content
