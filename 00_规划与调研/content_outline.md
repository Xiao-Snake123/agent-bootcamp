# 内容大纲：核心机制篇 12 章（深度版）

> 每章固定模块：目标 / 子主题 / 关键代码 demo 锚点（重生 agent_core 组件）/ 论文·文档锚点 / 面试题锚点 / 常见坑。
> 读者前提：熟悉 Python、会用 LLM API、了解 prompt 基本概念。

## 认知篇（前置，不单独成章，作首页+导论）
- Agent vs LLM App vs Workflow 的本质区别；自主度光谱。
- 成本-延迟-能力三角；何时该用 Agent、何时过度设计。
- 范式决策树：ReAct / Plan-Execute / Reflexion / Multi-Agent 选型。

---

## 第 1 章 推理-行动循环 ReAct
- **目标**：搞懂一个请求如何变成「思考→动作→观察」闭环。
- **子主题**：ReAct 原论文结构；thought/action/observation 三元组；终止条件；为何 lost-in-middle；循环的展开与压缩。
- **代码锚点**：`agent_core/agent.py` 的 `run()` 最小闭环（保留并深化）。
- **资料**：ReAct 2210.03629；Lilian Weng 综述 §2。
- **面试题**：① ReAct 与纯 prompt 链式调用区别？② 如何防止 Agent 死循环/无限调用？③ 长轨迹下上下文怎么管理？
- **坑**：把 observation 当普通文本拼接导致格式错乱；不做步数上限。

## 第 2 章 工具系统
- **目标**：工具是怎么被「声明—路由—调用—容错」的。
- **子主题**：Function Calling 协议（tool_calls 结构）；JSON Schema 校验；并行调用与聚合；重试/熔断/超时；human-in-the-loop 工具；工具结果回注。
- **代码锚点**：`agent_core/tools.py`（ToolRegistry）、`build_llm` 透传 tools。
- **资料**：OpenAI FC 文档；Toolformer 2302.04761。
- **面试题**：① 模型返回的 tool_calls 不可信时如何兜底？② 多工具并行如何合并结果？③ 工具报错如何设计可恢复？
- **坑**：schema 描述不清导致模型选错工具；未限制工具副作用。

## 第 3 章 上下文工程 Context Engineering
- **目标**：上下文窗口是 Agent 的「工作记忆」，怎么填、怎么省。
- **子主题**：system/user/tool 消息组织；KV 缓存命中；摘要压缩；短期记忆 vs 长期记忆；把 RAG 结果当作上下文的一部分；上下文优先级。
- **代码锚点**：`agent_core/memory.py`（短期/长期）、K4 重写。
- **资料**：Anthropic 上下文工程博文；Lilian Weng §4。
- **面试题**：① 上下文溢出有哪些策略？② 长期记忆检索与 RAG 的区别？③ 如何降低 token 成本又不影响效果？
- **坑**：把全部历史无脑塞回；忽略缓存命中导致延迟/成本翻倍。

## 第 4 章 规划与分解
- **目标**：复杂目标如何拆成可执行的任务结构。
- **子主题**：Plan-and-Execute；任务 DAG / 目标树；分解粒度；执行中重规划；回退与失败转移。
- **代码锚点**： planner 模块（新增）。
- **资料**：Tree of Thoughts 2305.10601；Plan-and-Solve 提示。
- **面试题**：① 规划与实际执行不一致怎么处理？② 分解过细/过粗的代价？
- **坑**：规划阶段不验证可行性；忽视依赖顺序。

## 第 5 章 反思与自修正
- **目标**：让 Agent 自我批评、用环境反馈纠错。
- **子主题**：Reflexion（ verbal reinforcement）；自我批评 prompt；验证器/单元测试作反馈；多轮修正上限。
- **代码锚点**：reflector 模块（新增，K6 深化）。
- **资料**：Reflexion 2303.11366；CRITIC。
- **面试题**：① 反思会不会陷入自我循环？② 如何区分「真错误」与「风格差异」？
- **坑**：反思无外部真值导致胡乱自我否定；无限重试烧钱。

## 第 6 章 多 Agent
- **目标**：多个 Agent 如何分工、通信、协同。
- **子主题**：角色协议与消息总线；Orchestrator 模式；辩论/共识；资源共享与死锁；与单 Agent 的边界。
- **代码锚点**：`agent_core/multi.py`（K7 深化）。
- **资料**：AutoGen 2308.08155；Generative Agents 2304.03442。
- **面试题**：① 何时该用多 Agent 而非单 Agent + 工具？② 多 Agent 通信瓶颈？③ 如何避免信息丢失/重复？
- **坑**：过度编排导致延迟叠加；消息无 schema 导致解析失败。

## 第 7 章 RAG 深度
- **目标**：检索增强的工程细节与失败模式。
- **子主题**：chunk 策略；embedding 选型；hybrid（BM25+向量）；rerank；查询改写；评测（recall/answer faithfulness）；失败模式（检索不到、上下文污染）。
- **代码锚点**：retriever/indexer（K8 升级为真实向量检索）。
- **资料**：LlamaIndex 文档；Self-RAG 2310.11511。
- **面试题**：① chunk size 怎么选？② 为什么需要 rerank？③ RAG 答非所问如何排查？
- **坑**：embedding 与查询语义不匹配；未做去重导致上下文冗余。

## 第 8 章 能力扩展（MCP / FC / Skill）
- **目标**：Agent 如何接入外部能力与知识，三者边界。
- **子主题**：Function Calling（协议层）、MCP（传输/标准化）、Skill/Plugin（封装层）；平台级能力；版本化；与 RAG/多 Agent 的边界。
- **代码锚点**：`tutorial/code/mcp_demo`、`skill_demo`（K9/K10 深化）。
- **资料**：MCP 官方规范；Anthropic tool use。
- **面试题**：① FC、MCP、Skill 三者的层级关系？② 为什么需要 MCP 标准化？
- **坑**：把 MCP 当万能胶，忽视鉴权/错误传播。

## 第 9 章 编排与框架
- **目标**：把前述模块串成可恢复、可观测的流水线。
- **子主题**：声明式图 vs 命令式；Node/Edge/checkpoint；human-in-the-loop 暂停；幂等；LangGraph/AutoGen/CrewAI 源码级对比；与第 4 章 Plan 的边界。
- **代码锚点**：`agent_core/orchestrator.py`（K11 深化）。
- **资料**：LangGraph 文档；Anthropic Building Effective Agents。
- **面试题**：① checkpoint 存哪些最小完备状态？② 幂等为什么是恢复命门？③ 自研 vs 用框架怎么选？
- **坑**：把编排逻辑写死在业务代码；恢复点不落盘。

## 第 10 章 评测与可观测
- **目标**：怎么知道 Agent 真的变好了。
- **子主题**：过程级 vs 结果级评估；轨迹回放；LLM-as-Judge；护栏（输入/输出/工具）；成本与延迟度量。
- **代码锚点**：`agent_core/eval.py`（K12 深化），复用 Trajectory。
- **资料**：AgentBench 2308.03688；Self-RAG 评测；PromptFoo。
- **面试题**：① 结果对但过程错的 Agent 算好吗？② LLM-as-Judge 的偏差如何缓解？
- **坑**：只看最终答案忽略过程；没有离线评估集就上线。

## 第 11 章 安全与合规
- **目标**：Agent 上线前的攻击面与防护。
- **子主题**：提示注入（直接/间接）；数据泄露（工具回传）；权限最小化；沙箱；红队；合规（PII/审计）。
- **代码锚点**：guardrail 模块（K12 深化）。
- **资料**：OWASP LLM Top 10；Anthropic 安全博文。
- **面试题**：① 间接提示注入如何防范？② 工具权限过大有何风险？
- **坑**：把用户输入直接拼进系统提示；工具无鉴权。

## 第 12 章 生产化 SRE
- **目标**：从 demo 到稳定服务。
- **子主题**：部署形态；流式输出；并发与限流；缓存（语义缓存）；降级（模型/工具故障）；监控告警；成本治理。
- **代码锚点**：`agent_core/serve.py`（FastAPI 封装，供问答助手复用）。
- **资料**：各厂 LLMOps 实践；LiteLLM。
- **面试题**：① 如何做语义缓存提升命中？② Agent 服务如何限流与降级？
- **坑**：无超时导致雪崩；忽视流式下的错误传播。

---

## 实战篇（贯穿项目）
- 重生 `agent_core`：LLM/工具/记忆/检索/编排/评测 统一接口。
- 接真实 LLM + 工具 + 记忆 + RAG（DeepSeek 真跑）。
- 多 Agent 协作案例 + 评测 + 上线检查单。

## 求职篇（阶段 5）
- 知识点图谱（按岗位：算法/后端/ML/AI 应用）。
- 高频面试题 + 标准答案思路（概念/对比/陷阱）。
- Agent 系统设计题（设计一个 Agent 平台）。
- 简历项目包装话术。
