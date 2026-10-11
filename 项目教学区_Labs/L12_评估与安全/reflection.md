# L12 Reflection（对应 K12）

## 1. 这次实现了什么
- K12 理论：过程级 vs 结果级评估、Trajectory 回放、分层护栏（输入/输出/权限/预算）、可观测、2025–2026 实务（LLM-as-judge、LangSmith/Langfuse、红队、过程级为何更重要、与 K11 轨迹复用）、5 条陷阱、开放题（客服 Agent 评估与护栏）。
- L12 落地一个**评估与安全面板**：`eval_panel.py` 的 `Guardrail`（危险指令拦截 + 密钥/密码泄露检测）、`Budget`、`CostMeter`、`score_process/score_outcome`；`loop.py` 演示三场景（正常打分 / 危险输入拦截 / 超预算截断）；`test_eval.py` 五项验收。

## 2. 关键设计决定（为什么）
- **评估消费 K11 的 Trajectory**：不另造日志，直接复用 `agent_core.Trajectory`——K11 编排的节点/checkpoint 轨迹点天然成为 K12 的评估证据，闭合 P6（design_docs 的 K11+K12 收口）。
- **护栏分层且可分级**：输入（挡危险/注入）、输出（挡泄露）、预算（挡跑飞）——二态拦截先跑通，README 技能演练② 指引升级为"警告/拦截"分级，避免过严不可用（陷阱②）。
- **评分接口预留 LLM-as-judge**：规则评分可解释、离线可跑；但 `score_*` 签名对轨迹，技能演练① 可直接换成评委模型，呼应 2025–2026 主流。
- **过程级独立打分**：`score_process` 逐步骤核（thought+action/observation 且非失败），专门抓"路径质量"，对应 K12 核心认知"过程级比结果级更重要"。

## 3. 前沿点（K12 落地）
- **LLM-as-judge 就绪**：评分函数与具体评委解耦，一键切换强模型。
- **可观测底座**：Trajectory + CostMeter 是 LangSmith/Langfuse 的最小本地等价物（技能演练④）。
- **与 K11 协同**：编排器产轨迹 → 评估器消费轨迹 → 护栏总闸可嵌回编排，形成"跑→记→评→守"闭环。
- **生产护栏雏形**：危险指令 + 泄露检测 + 预算三重防线，正是红队/上线前标配。

## 4. 若重做会改什么
- 接入真实 LLM-as-judge（技能演练①）与分级护栏（②）。
- 在 K11 编排里挂本面板为总闸（③），闭合 P6。
- 导出兼容 Langfuse 的轨迹格式（④），迈向生产可观测。
- 至此 K1–K12 全部完成，下一步进入 P7 大项目 Capstone：把 `agent_core`（工具/记忆/规划/反思/多智能体/RAG/MCP/Skill/编排/评估）整合成端到端系统。
