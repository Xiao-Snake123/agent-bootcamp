# 第 8 章 能力扩展：Function Calling / MCP / Skill

> 难度：★★★☆☆ ｜ 前置：第 2 章 ｜ 对应旧 K9/K10

## 8.1 三者解决不同层级的问题
初学者容易混淆，先厘清层级：
- **Function Calling (FC)**：**协议层**——模型如何"表达想调某个函数"（tool_calls 结构）。是模型能力，不是传输。
- **MCP (Model Context Protocol)**：**传输/标准化层**——工具的定义、调用、结果如何在"模型端 ↔ 工具服务端"之间标准化流动，解决"每个工具都要定制对接"的碎片化。
- **Skill / Plugin**：**封装层**——把一组工具+提示+流程打包成"可复用能力单元"（如"发邮件技能"含草稿/发送/追踪多个工具）。

## 8.2 Function Calling 是底座
第 2 章的工具系统本质就是 FC 的工程化：声明 schema、模型返回 tool_calls、执行回注。FC 是模型侧原语，MCP/Skill 都建立在"模型能 FC"之上。

## 8.3 MCP：为什么需要标准化
没有 MCP 时，每接一个工具（GitHub/Slack/数据库）都要写一套适配（鉴权、参数映射、结果解析）。MCP 定义统一协议：
- **Host**（如 IDE/Agent 运行时）连接 **Server**（工具提供方）。
- Server 暴露 `tools` / `resources` / `prompts`，通过标准 JSON-RPC 通信。
- 好处：工具一次实现、到处接入；权限与错误传播标准化。
```json
// MCP server 暴露的工具描述（与 FC schema 同构，但走标准传输）
{"name":"create_issue","description":"在仓库建 issue","inputSchema":{...}}
```
注意：MCP 不改变"模型怎么选工具"，只标准化"工具怎么被接入和调用"。

## 8.4 Skill / Plugin：能力打包
Skill = 更高层抽象：把"调哪些工具 + 用什么提示 + 什么顺序"封装成一个命名能力，供 Agent 按名调用或自动匹配。类比：FC 是函数指针，Skill 是"功能模块/库"。
- 例：`email_skill` 内含 draft/send/track 三个 FC 工具 + 一套邮件礼仪提示。
- 价值：降低 Agent 决策面（选"发邮件技能"比选 3 个底层工具简单），便于权限与版本管理。

## 8.5 与 RAG / 多 Agent 的边界
- MCP/Skill 解决"**接什么能力**"；RAG 解决"**喂什么知识**"；多 Agent 解决"**谁来干、怎么协作**"。三者正交，可组合（如一个 Skill 内部用 RAG 取数，再由 Orchestrator 派给某 Agent）。

## 8.6 工程实践
- 自研工具：直接用 FC（第 2 章）即可，不必上 MCP。
- 接第三方/多客户端：用 MCP 省适配成本（GitHub/Slack/Notion 都有现成 MCP server）。
- 复用复杂流程：抽成 Skill 供多个 Agent 共享。

## 8.7 资料
- MCP 官方规范：https://modelcontextprotocol.io
- Anthropic tool use 文档（FC 细节）

## 8.8 面试考点
1. **FC、MCP、Skill 三者的层级关系？** 答：FC=模型表达调函数的协议层；MCP=工具接入/传输的标准化层；Skill=工具+提示+流程的封装层。由低到高。
2. **为什么需要 MCP 标准化？** 答：避免每个工具定制适配，统一鉴权/错误/传输，工具一次实现处处接入。
3. **什么时候该抽 Skill 而不是堆工具？** 答：当一组工具总是被一起调用、需要统一权限/版本/提示时，抽 Skill 降低决策面。

## 8.9 常见坑
- **把 MCP 当万能胶** → 忽视鉴权透传与错误传播，工具报错被吞。
- **Skill 过度封装** → 黑盒化导致调试困难、粒度不匹配。
- **FC schema 与 MCP 描述不一致** → 模型按 FC 填参，MCP server 解析失败。
