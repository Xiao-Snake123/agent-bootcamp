# L11 Reflection（对应 K11）

## 1. 这次实现了什么
- K11 理论：声明式图编排 vs 命令式 if/for、Node/Edge/checkpoint/human-in-the-loop/幂等、2025–2026 实务（LangGraph/AutoGen/CrewAI 对照、与 K5 Plan 的区别、幂等是恢复命门、可观测钩子）、5 条陷阱、开放题（报销审批流）。
- L11 落地一个**纯 Python 图编排引擎**：`orchestrator.py` 的 `Node/Graph` 支持条件边、`checkpoint` 落盘恢复、人工节点暂停（PAUSED_FOR_HUMAN）、`done` 列表保证幂等；`loop.py` 把 Planner→Executor→Critic→人工审批串成流水线并演示中断恢复；`test_orchestrator.py` 四项验收。

## 2. 关键设计决定（为什么）
- **纯 Python 不引重框架**：design_docs 明确"K11 前不引入重框架"；本引擎是 LangGraph 的极简内核映射，聚焦机制而非工程封装，便于从零理解。
- **checkpoint 存 current+data+done**：三者是断点续跑的最小完备集——知道"现在在哪、数据怎样、哪些已做"，才能安全恢复。
- **人工节点先落 checkpoint 再暂停**：保证"暂停点"可恢复，对应 K11 护栏与可问责（陷阱⑤）。
- **`done` 列表做幂等**：恢复/重跑时已完成节点跳过副作用（如 `_side_effects` 计数），直接防"重复扣款/重复发信"（陷阱②）。
- **节点可替换为 K3–K10 模块**：`loop.py` 用 Mock，但 README 明写 planner→K5、executor→K3/K9、critic→K6、人工→K12，体现"编排是骨架、模块是血肉"。

## 3. 前沿点（K11 落地）
- **与 K5 Plan-and-Execute 的边界**：Plan 是单 Agent 内部拆解；Orchestrator 是跨模块/跨 Agent 调度骨架——本 Lab 首次把"调度层"独立出来，呼应 K5 所述"规划是连接推理/工具/记忆的调度层"。
- **LangGraph 内核映射**：StateGraph/节点/条件边/interrupt/checkpoint 逐一对应，技能演练④ 直接对照。
- **为 K12 铺路**：每个节点进出与 checkpoint 落盘都是天然轨迹点，K12 评估/回放可直接复用。

## 4. 若重做会改什么
- 加**回边/循环**（技能演练①）：驳回回到 executor，更贴近真实审批。
- 加**持久化后端**（技能演练③）：checkpoint 换 DB/S3，生产级恢复。
- 在 K12 里把本编排器接入评估/护栏，闭合 P6（K11+K12）。
