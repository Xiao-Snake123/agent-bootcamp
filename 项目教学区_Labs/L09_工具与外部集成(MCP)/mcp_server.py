"""L09 最小 MCP server（离线 in-process 近似）。

真实 MCP server 通过 JSON-RPC over stdio/SSE 暴露能力；本 Lab 用同进程对象
近似其协议面：initialize / tools/list / tools/call，便于无子进程跑通与 pytest。
真实 stdio 实现可对照 tutorial/code/mcp_demo/。
"""

from typing import Dict, Any, List


class MCPTool:
    def __init__(self, name: str, description: str, schema: dict, handler):
        self.name = name
        self.description = description
        self.schema = schema            # {"properties": {...}}
        self.handler = handler          # callable(**args) -> str

    def to_schema(self) -> Dict[str, Any]:
        return {"name": self.name, "description": self.description,
                "input_schema": self.schema}


class MCPServer:
    def __init__(self):
        self.tools: List[MCPTool] = []
        self.initialized = False

    def register_tool(self, tool: MCPTool):
        self.tools.append(tool)

    # —— 协议三原语（JSON-RPC 方法的离线等价）——
    def initialize(self) -> str:
        self.initialized = True
        return "ok"

    def list_tools(self) -> List[Dict[str, Any]]:
        return [t.to_schema() for t in self.tools]

    def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        if not self.initialized:
            raise RuntimeError("未 initialize，不能调用")
        for t in self.tools:
            if t.name == name:
                return t.handler(**args)
        raise KeyError(f"未知工具：{name}")


# —— 示例远端工具（真实应跨进程暴露）——
def _weather_handler(city: str) -> str:
    return f"{city} 今天晴，气温 25℃。"


def build_demo_server() -> MCPServer:
    srv = MCPServer()
    srv.register_tool(MCPTool(
        "weather", "查询城市天气",
        {"properties": {"city": "城市名"}},
        _weather_handler,
    ))
    return srv
