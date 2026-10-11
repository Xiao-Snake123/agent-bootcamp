# L08 Reflection（对应 K08）

## 1. 这次实现了什么
- K08 理论：RAG 两阶段 pipeline、chunk/embedding/retrieval/rerank/query-rewrite/citation、2025–2026 实务（hybrid 检索、cross-encoder 重排、HyDE/sub-query、出处标注、长上下文 vs RAG、与 K4 记忆同构、RAGAS）、6 条陷阱、开放题（公司制度问答）。
- L08 落地离线 **RAG 全流程**：`indexer.py`（按句切片建库）、`retriever.py`（BM25 近似 top-k 召回）、`generator.py`（拼接注入 + `[id:source]` 出处标注）；`loop.py` 用本地小语料演示"年假"问题检索到制度片段并带出处回答。

## 2. 关键设计决定（为什么）
- **离线 BM25 近似替代 embedding 检索**：无 Key、可跑通机制；中文按字/英文按词取交集打分，结构等价于真实向量召回（技能演练①换真向量库）。
- **出处标注是默认动作**：`Generator` 强制把 chunk id + source 拼进答案——直接对应 K8 陷阱③"不标注来源则幻觉难查"，让证据可审计。
- **两阶段清晰分离**：建库（离线）与检索生成（在线）解耦，真实部署时只需把 `Indexer/Retriever` 换成向量库，下游不变。
- **与 K4 记忆同构**：检索注入的机制和 K4 长期记忆检索注入一致——本 Lab 在 README 技能演练③中提示统一为"Agentic RAG"。

## 3. 前沿点（K8 落地）
- **Hybrid + Rerank**：当前是单路 BM25；真实应 BM25+向量融合初检、cross-encoder 精排（技能演练①），这是 2025 RAG 的默认最优形态。
- **Query Rewrite / HyDE**：检索前改写查询显著提升召回（技能演练②）。
- **长上下文不替代 RAG**：本 Lab 用"小语料+检索"印证——RAG 提供可验证出处与可热更新知识，不同于把全部文档塞进长窗口。
- **Grounded Generation**：模板拼接即"答案必须基于检索内容"的雏形；真 LLM 时应约束不得超出检索范围。

## 4. 若重做会改什么
- 把 `Retriever` 换成真实 embedding + 向量库，并加 hybrid 与 rerank（技能演练①）。
- 加 `QueryRewriter`（LLM 改写）提升难查询召回（技能演练②）。
- 接入 K7 Orchestrator 做 Agentic RAG：规划"何时/检索什么"，并把 K4 记忆作为第二检索源，闭合"规划—检索—记忆—生成"全链路。
