# L09 Reflection（对应 K09）

## 1. 这次实现了什么
- K09 理论：MCP 是什么/解决什么、协议三原语（tools/resources/prompts）、核心方法（initialize/list_tools/call_tool）、Agent↔client↔server 接入时序、与 K3 FC 的关系（传输层 vs 调用协议）、2025–2026 实务（MCP 成标准、transport 选择、与 A2A/RAG/多 Agent 关系、auth）、5 条陷阱、开放题（天气 server 设计）。
- L09 落地一个**最小 MCP 接入**：`mcp_server.py`（initialize/list_tools/call_tool 离线近似 + weather 示例）、`mcp_bridge.py`（把远端 schema 翻译为本地 `Tool` 注册进 `ToolRegistry`）、`loop.py` 演示 Agent 无感调用远端工具。

## 2. 关键设计决定（为什么）
- **离线 in-process 近似协议**：用同进程对象实现三个 JSON-RPC 方法的等价行为，无需子进程/网络即可 pytest 与演示；真实 stdio/SSE 在 README 技能演练①对照 `tutorial/code/mcp_demo/`。
- **bridge 翻译落点同本地工具**：`_RemoteTool.run` 内部经 `server.call_tool` 转发，外部与本地 `Tool` 完全同构——直接印证 K9"入口不同、落点相同，Agent 主循环无感"。
- **schema 映射闭环**：远端 `input_schema.properties` 映射到本地 `Tool.schema`，保证 `ToolRegistry.dispatch` 的参数清洗不脱节（陷阱③）。
- **未初始化拒绝调用**：`call_tool` 前检查 `initialized`，模拟真实握手的顺序约束。

## 3. 前沿点（K9 落地）
- **MCP 成工具接入标准**：本 Lab 把"即插即用远端能力"的机制跑通；2025 大量系统提供官方 MCP server，价值在标准化而非又一种调用方式（陷阱①）。
- **三原语完整度**：当前只做 tools；resources（上下文）/prompts（模板）是 MCP 比"只有工具"更完整之处（技能演练②）。
- **auth/权限边界**：远端工具带副作用，必须鉴权+最小权限（陷阱④），技能演练③补上。
- **与 K8/K7 同构**：RAG 检索、多 Agent 角色能力都可暴露成 MCP tool，统一接入——本 Lab 在 README/reflection 点明。

## 4. 若重做会改什么
- 把 `MCPServer` 升级为真实 JSON-RPC over stdio/SSE，bridge 跨进程连接（技能演练①），与 `tutorial/code/mcp_demo/` 对齐。
- 扩展 `MCPBridge` 支持 resources/prompts 原语（技能演练②），让 Agent 也能取远端上下文与提示模板。
- 在 bridge 加 auth 头、超时与重试（技能演练③），闭合权限边界陷阱。
