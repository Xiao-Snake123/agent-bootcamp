# 核心机制篇配套可运行 demo（阶段 3）

12 章各一个**能真跑**的最小实现，统一构建在顶层 `agent_core/`（v2 重生包）之上。
与网页模块一一对应：`/modules/01` … `/modules/12`。

## 运行约定

```bash
# 离线一键自检 12 个（零费用、不需要 key，推荐提交前跑）
python demos/run_all.py

# 单个 demo：有 DEEPSEEK_API_KEY 时自动接真实 deepseek-chat
python demos/demo_01_react.py

# 强制离线（可脚本化 Mock，不联网）
python demos/demo_01_react.py --offline

# 覆盖提问目标 / 收紧预算 / 第7章启用向量检索
python demos/demo_07_rag.py --goal "hybrid 检索怎么融合" --max-cost 0.05 --vector
```

**安全护栏**（`_shared.py` 统一提供）：

- 默认预算 `AGENT_MAX_COST=0.30` 元，超限由 `CostLimitError` 截断；
- 每个 demo 都有 `max_steps` 上限，`Agent` 内置重复调用检测（默认 3 次）；
- 单价 `LLM_PRICE_IN` / `LLM_PRICE_OUT`（元/百万 token）仅作护栏估算，**以账单为准**；
- `--offline` 或缺少 key 时自动降级 `MockLLMClient`，脚本化模拟原生 Function Calling。

## 章节 → demo → agent_core 模块

| 章 | demo 文件 | 主要模块 | 看什么 |
| --- | --- | --- | --- |
| 1 | `demo_01_react.py` | `Agent`, `ToolRegistry` | 原生 FC 协议回注 `assistant(tool_calls) → tool(tool_call_id)` |
| 2 | `demo_02_tools.py` | `ToolRegistry`, `openai_schemas()` | JSON Schema、并行 tool_calls、参数校验与错误回填 |
| 3 | `demo_03_context.py` | `BufferMemory`, `SummaryMemory` | 稳定前缀（KV 缓存）、真 LLM 摘要压缩、上下文预算 |
| 4 | `demo_04_planning.py` | `Planner`, `Plan`, `PlanStep` | 依赖 DAG 拓扑执行、失败重规划 |
| 5 | `demo_05_reflexion.py` | `Reflector`, `Trajectory` | 客观轨迹复盘、经验注入、重试上限 |
| 6 | `demo_06_multiagent.py` | `MultiAgent`, `Blackboard` | 结构化消息、共享黑板、死锁/推诿检测 |
| 7 | `demo_07_rag.py` | `Indexer`, `HybridRetriever` | markdown 切块、BM25 + 可选向量、RRF 融合、生成 |
| 8 | `demo_08_mcp_skill.py` | `ToolRegistry` + tutorial MCP server | 真实 stdio JSON-RPC 子进程、工具映射、Skill frontmatter |
| 9 | `demo_09_orchestrator.py` | `Graph`, `once` | 拓扑调度、checkpoint 恢复、幂等副作用、HITL |
| 10 | `demo_10_eval.py` | `TrajectoryEvaluator`, `EvalCase` | 复用轨迹的多维可解释评测 |
| 11 | `demo_11_guardrail.py` | `Guardrail`, `GuardedToolRegistry` | 注入检测、最小权限、危险参数、输出泄露防护 |
| 12 | `demo_12_serve.py` | `agent_core.serve.create_app` | FastAPI `/health` `/chat` `/run_agent` |

## 与 v1 的区别（为什么"重生"）

旧 `项目教学区_Labs/agent_core/` 保留作归档，但它有三个致命问题，v2 已修复：

1. `complete() -> str` 丢弃 `tool_calls` → v2 新增 `chat()` 返回完整 `ChatResponse`；
2. `Agent.run()` 手写 `{action,args}` JSON、`role=tool` 无 `tool_call_id`，**真实 DeepSeek 必 400** → v2 走标准协议；
3. 成本护栏 `unit_price=0.0` 永不触发 → v2 用可配置真实单价 + 预算预检。

另：v1 的 L01–L12 全是 Mock 硬编码玩具；v2 的 demo 默认接真实 DeepSeek（也可离线自检）。

## 依赖

见项目根 `requirements.txt`。最小：`openai>=1.0`、`python-dotenv`；
第 12 章的 `TestClient` 需要 `fastapi` + `httpx`；第 7 章 `--vector` 需要 DashScope key。

## HTTP 服务

```bash
uvicorn agent_core.serve:app --port 8001
# GET /health  |  POST /chat {"goal":"..."}  |  POST /run_agent {"goal":"..."}
```
