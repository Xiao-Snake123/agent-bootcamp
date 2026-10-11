# L04 Reflection（对应 K04）

## 1. 这次实现了什么
- 在 `agent_core/memory.py` 升级出两层记忆：`BufferMemory`（短期滑窗 + 自动 compaction）与 `LongTermMemory`（长期 KV 库 + 离线语义召回近似）。
- `memory_tools.py` 把长期记忆包成 `SaveFact`/`Recall` 两个工具，让 Agent 通过动作显式读写——这就是 **agentic memory** 的最小形态。
- `loop.py` 用 `MemoryMock` 演示**跨会话记住用户名**：两次 `run` 共享同一个 `LongTermMemory`，第二次问"我叫什么"能从长期记忆召回，尽管它的上下文窗口里根本没有第一次的对话。

## 2. 关键设计决定（为什么）
- **记忆不进上下文，靠检索注入**：第二次 run 的 `messages` 只有本次 goal + 工具观察，第一次的话不在窗口里。Agent 之所以"记得"，是因为 `Recall` 工具从长期记忆取回并作为观察注入——直接印证 K4"长期记忆≠上下文"。若把历史全塞 system，会回到 lost-in-the-middle 与爆窗。
- **长期写入要显式/有选择**：`LongTermMemory.add(step)` 故意空实现，不让每步观察无差别灌进长期记忆（陷阱③噪声淹没）。只有 Agent 调 `SaveFact` 才写——对应"agentic memory 要会决定存什么"。
- **namespace 隔离**：`LongTermMemory(namespace=...)` 预留按用户隔离，避免跨会话污染（陷阱⑥）。
- **短期自动 compaction**：`BufferMemory` 超 `window` 自动把旧片段折叠成摘要句，而非无限累积——K2 lost-in-the-middle 的前端防线。

## 3. 前沿点（K4 落地）
- **agentic memory**：写记忆不是工程师写死，而是 Agent 经决策/反思"自己决定"。本 Lab 用工具让 Agent 显式存/取，是这一思想的离线最小实现；真实系统如 **mem0** 会自动抽取/去重/更新用户事实，**MemGPT/Letta** 用操作系统式分层（主上下文=寄存器、外部存储=磁盘）自主搬移记忆。
- **compaction 真实做法**：本 Lab 用拼接近似；生产应交给小模型递归摘要（"摘要的摘要"），主模型只看浓缩上下文。
- **真实语义召回**：`recall` 现在是子串回退，真实应接 embedding + 向量库（Qdrant/Pinecone）做 cosine/hybrid top-k——这是 K8 RAG 的同款机制，记忆可视为"Agentic RAG"。
- **隐私/遗忘**：长期记忆写用户 PII 需有清理与合规策略（K12）；陷阱④提醒别无脑留存。

## 4. 若重做会改什么
- 把 `LongTermMemory.recall` 升级为真实向量召回（见 README 技能演练）。
- 给 `BufferMemory` 的 compaction 接一个真摘要模型（或在 K5 规划里统一用反思模块生成摘要）。
- 让 `Agent.run` 在每轮把 `BufferMemory` 的近期内容自动注入 system，形成"短期记忆参与决策"的闭环（目前 L4 只为演示分层，未自动注入）。
