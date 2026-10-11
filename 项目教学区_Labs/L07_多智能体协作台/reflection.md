# L07 Reflection（对应 K07）

## 1. 这次实现了什么
- K07 理论：多智能体适用场景与代价、role/message bus/orchestrator/handoff、三种拓扑（流水线/辩论/评审）、2025–2026 实务（AutoGen/CrewAI/LangGraph、角色专业化、human-in-the-loop、与 K5/K6 组合）、5 条陷阱、开放题（市场分析报告三角色系统）。
- L07 落地一个**多智能体协作台**：`message_bus.py`（解耦消息）、`roles.py`（Researcher/Writer/Critic 三角色）、`orchestrator.py`（流水线 + 评审循环 + `max_rounds` 终止）；`loop.py` 演示 Critic 首轮"需修改"触发 Writer 重修、次轮"通过"。

## 2. 关键设计决定（为什么）
- **角色解耦 + message bus**：角色只读写 bus，不直接互相调用，避免 K7 陷阱③"上下文互灌爆炸"——每个角色按需 `last_from` 取必要上下文，而非全量历史。
- **Orchestrator 集中路由 + 显式终止**：把"谁在何时行动"收口到编排者，并用"通过"信号 / `max_rounds` 双保险终止（陷阱②无终止条件）。
- **Critic 与 Actor 分离**：Writer 产、Critic 批，角色专业化也减少自评偏见（呼应 K6）；评审循环即 K6 反思在多角色下的表达。
- **离线 mock 跑通骨架**：三角色用规则产出，真场景换 `OpenAIClient`（README 技能演练①），编排/总线不动。

## 3. 前沿点（K7 落地）
- **角色专业化 + 协作溢价**：拆"研究/写作/评审"让每个提示更短易调；但简单任务单 Agent 更省（陷阱④）——本 Lab 用三角色演示"专业化值得"的边界。
- **与 K5/K6 组合**：Orchestrator 可内含 planner（K5）与 reflector（K6），升级为"规划—执行—反思"的多角色版（技能演练③）。
- **Human-in-the-loop**：发布前在 Critic 处插人审，避免多 Agent 自说自话（K7 实务）。
- **拓扑可扩展**：当前实现流水线+评审；辩论拓扑只需新增环形驱动（技能演练②）。

## 4. 若重做会改什么
- 把 `Orchestrator` 升级为复合编排者：先 K5 planner 拆子任务 → 分给角色 → 角色产出经 K6 reflector 自评 → handoff 下一角色，闭合全链路。
- 加 `DebaterA/B` 与环形驱动，补上 K7 的"辩论拓扑"。
- 在 K11 编排章节把总线/编排迁移到图（LangGraph 对照），统一可中断恢复。
