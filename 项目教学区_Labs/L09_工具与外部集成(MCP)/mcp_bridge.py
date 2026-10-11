"""L09 MCP 桥接：把远端 MCP server 的工具"翻译"成本地 agent_core Tool，注册进 Registry。

对应 K9 伪代码 bridge()：initialize → list_tools → wrap_as_local_tool → register。
落点同本地工具，Agent 主循环无感（K9 关键认知：传输层 vs K3 FC 调用协议）。
"""

from agent_core.tools import Tool, Observation


class _RemoteTool(Tool):
    def __init__(self, schema: dict, server):
        self.name = schema["name"]
        self.description = schema.get("description", "")
        self.schema = {"properties": schema.get("input_schema", {}).get("properties", {})}
        self._server = server

    def run(self, **kwargs) -> Observation:
        try:
            result = self._server.call_tool(self.name, kwargs)
            return Observation(content=result)
        except Exception as e:
            return Observation(content=f"MCP 工具 {self.name} 调用失败：{e}", ok=False)


class MCPBridge:
    def __init__(self, server):
        self.server = server

    def connect(self):
        self.server.initialize()

    def register_into(self, registry):
        for schema in self.server.list_tools():
            registry.register(_RemoteTool(schema, self.server))
        return registry
