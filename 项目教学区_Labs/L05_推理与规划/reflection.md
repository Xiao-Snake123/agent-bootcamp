# L05 Reflection（对应 K05）

## 1. 这次实现了什么
- K05 理论：推理 vs 规划、ReAct 与 Plan-and-Execute 结构差异、2025–2026 实务（推理模型 o1/o3/R1 对规划层的冲击、plan mode、可验证子目标、replanning）、6 条陷阱、开放题。
- L05 落地一个**解耦的 Plan-and-Execute 骨架**：`planner.py`（Planner + MockPlanner）只负责把目标拆成子目标；`executor.py`（PlanExecutor）只负责按 plan 逐步执行，执行单元 `step_fn` 可插拔（真 Agent / 工具 / 函数）；`loop.py` 把 Plan-and-Execute 与 ReAct（`agent_core.Agent` 自带）对照演示。

## 2. 关键设计决定（为什么）
- **规划与执行解耦**：Planner 不碰执行细节，Executor 不碰拆目标。这样执行单元能随时换成真 Agent（如带工具的 `Agent.run`）或真实工具——对应 K5"规划是连接推理/工具/记忆的调度层"。
- **MockPlanner 用规则拆"并/然后"**：离线即可演示复合目标拆步，无需 LLM；同时保留 `Planner(ABC)` 接口，真 LLM planner 可无缝替换（README 技能演练①）。
- **执行单元可插拔 `step_fn`**：最小化耦合，测试能用 `lambda s: f"done:{s}"` 跑通，不依赖联网或复杂工具。
- **对照 ReAct 而非只讲一种**：用同一个目标分别走两种范式，直观体现 K5"任务一复杂、出错代价高时，Plan-and-Execute 更稳"。

## 3. 前沿点（K5 落地）
- **推理模型的边界**：o1/o3/R1 强化了"单步难推理"，但多步编排（拆解、工具调度、状态/记忆管理）仍靠规划层——本 Lab 的 Planner 即这一层的最小形态。
- **可验证子目标**：MockPlanner 的默认三步含"复核结果"，雏形即 K5 强调的"每步要有可验证产出"。真 LLM planner 应让每步带 `verify` 字段（技能演练①）。
- **Replanning on failure**：当前 Executor 线性跑完；K5 陷阱②提醒要加 replan——技能演练②即把它补上（失败时基于已完成结果重新规划剩余步骤）。
- **Plan Mode**：本 Lab 把"先 plan 再 execute"显式分离，正是 plan mode 思想（先出方案可复核/可等人确认）的代码表达。

## 4. 若重做会改什么
- 把 `step_fn` 默认接 `agent_core.Agent`（带工具）而非占位 lambda，让每个子目标本身也是一次 ReAct，形成"规划层 + 执行层都基于 Agent"的两级结构。
- 给 `PlanExecutor` 加 `verify` 钩子与 `replan` 分支（技能演练②），闭合 K5 的"可验证 + replan"工程闭环。
- 在 K7 反思章节接入后，让 planner 在 replan 时调用反思模块分析失败原因。
