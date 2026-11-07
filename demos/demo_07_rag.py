"""第 7 章 · RAG 深度：切块 → hybrid 检索 → 拼上下文 → 生成。

默认纯 BM25（零成本）；``--vector`` 且配置了 DASHSCOPE_API_KEY 时，
额外启用 DashScope embedding，用 RRF 融合 BM25 与向量排名。
文档：content/核心机制篇/07_RAG深度.md
"""
from _shared import (CONTENT_DIR, HybridRetriever, Indexer, get, run)


def _dashscope_embed_fn():
    from openai import OpenAI
    client = OpenAI(
        api_key=get("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = get("DASHSCOPE_EMBED_MODEL", "text-embedding-v3")

    def embed(texts):
        out = []
        for i in range(0, len(texts), 8):   # DashScope 单次批量上限 <=10
            resp = client.embeddings.create(model=model, input=texts[i:i + 8])
            out.extend(d.embedding for d in resp.data)
        return out

    return embed


def body(llm, args):
    indexer = Indexer.from_dir(str(CONTENT_DIR))
    print(f"索引：{len(indexer.documents)} 个文档块（来自 content/核心机制篇/*.md）")

    embed_fn = None
    if args.vector and get("DASHSCOPE_API_KEY"):
        embed_fn = _dashscope_embed_fn()
        print("检索模式：hybrid（BM25 + DashScope 向量，RRF 融合）")
    else:
        print("检索模式：BM25（加 --vector 可启用向量融合）")

    retriever = HybridRetriever(indexer.documents, embed_fn=embed_fn)
    query = args.goal or "RAG 为什么需要 rerank，hybrid 检索有什么好处？"
    hits = retriever.search(query, top_k=3)
    print("\n召回结果：")
    for i, hit in enumerate(hits, 1):
        print(f"  {i}. [{hit['title']}] score={hit['score']} | {hit['text'][:80]}...")

    context = "\n\n".join(h["text"][:500] for h in hits)
    prompt = ("仅基于以下资料回答，标注引用来源，不要编造。\n\n"
              f"资料：\n{context}\n\n问题：{query}")
    answer = llm.complete([
        {"role": "system", "content": "你是严谨的 RAG 助手，答案必须忠于给定资料。"},
        {"role": "user", "content": prompt}])
    print("\n生成答案：", answer[:400])
    print("要点：召回多、精排少；chunk 大小与 overlap 需用检索评测反调，而非拍脑袋。")


if __name__ == "__main__":
    run(7, "RAG 深度（hybrid 检索 + 生成）", body,
        script=["（离线）rerank 把召回的 top-20 精排到 top-5；"
                "hybrid 融合 BM25 的精确匹配与向量的语义召回，提升最相关块命中率。"])
