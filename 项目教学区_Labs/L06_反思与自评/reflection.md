# L06 Reflection（对应 K06）

## 1. 这次实现了什么
- K06 理论：反思/自评必要性、可执行反馈 vs 语言反馈、反思闭环结构与收敛、2025–2026 实务（Reflexion、LLM-as-judge、self-consistency、Critic/Actor）、6 条陷阱、开放题（SQL 自检闭环）。
- L06 落地一个**可执行反思闭环**：`reflector.py` 用真实 `compile` 校验代码语法（确定信号）；`self_correct_loop.py` 反复 生成→反思→回填反馈→再生成，直到通过或 `max_iter`；`loop.py` 用离线生成器演示"含错代码→自检→修正"。

## 2. 关键设计决定（为什么）
- **用 compile 做"可执行反馈"**：直接印证 K6"可执行反馈比语言反馈可靠"——模型不会靠"嘴上说改好"骗过闭环（陷阱②自我欺骗被破解）。这是本 Lab 与纯语言反思的本质区别。
- **反馈回填生成器**：`SelfCorrectLoop` 把 `reflect()` 的 feedback 传给下一轮 `generate(goal, feedback)`，让修正有依据，而非盲目重生成。
- **强制 max_iter 上限**：防止反思不收敛空转（陷阱①）；达到上限返回当前最佳并标注"未通过"。
- **生成器可插拔**：`generator` 是 `callable(goal, feedback)`，离线用 mock，真场景可换 `OpenAIClient`（README 技能演练②），不改动闭环骨架。

## 3. 前沿点（K6 落地）
- **Reflexion 与 K4 记忆合流**：本 Lab 把"反思"作为独立闭环；真实系统（Reflexion）会把反思文本写入长期记忆，下次避开同类错。技能演练③即把"常见错误→修正"写入 `LongTermMemory`，闭合链路。
- **可执行验证层级**：compile（语法）→ exec（运行时）→ 单测/断言，验证越强越可靠；本 Lab 用 compile 打底，技能演练①升级为 exec 运行反思。
- **LLM-as-judge 的边界**：可加一层模型打分，但必须记住 judge 也会错（陷阱⑤），不可替代可执行信号。
- **与 K5 构成闭环**：K5 的 plan/replan 是"事前想清楚"，K6 反思是"事后复盘改"——规划—执行—反思三段式。

## 4. 若重做会改什么
- 把 `SelfCorrectLoop` 接到 L5 的 `PlanExecutor`：每个子目标执行后跑一次反思，形成"规划层 + 执行层 + 反思层"三级 Agent（呼应 design_docs 的 L6 任务分解执行器）。
- 加"运行反思"（exec 沙箱）与"记忆回填"（Reflexion），让教训跨会话复用。
- 在 K11 评估章节把 `Reflector` 换成可量化的评分 judge，统一评估口径。
