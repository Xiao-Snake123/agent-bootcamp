"""离线验证检索 + 生成链路（不启服务，用于快速检验原型逻辑）。"""
import rag_server as r

if __name__ == "__main__":
    print(f"已加载 {r.N} 个 chunk\n")
    for q in [
        "Agent 如何防止死循环和无限调用工具？",
        "RAG 为什么需要 rerank？",
        "多 Agent 什么时候该用，和单 Agent 加工具的区别？",
        "上下文工程里 KV 缓存为什么重要？",
        "生产化里语义缓存怎么提升命中？",
    ]:
        print("Q:", q)
        chunks = r.bm25(q, 3)
        for c in chunks:
            print(f"   - [{c['chapter']} / {c['section']}] {c['text'][:40]}…")
        print("   A(前120字):", r.generate(q, chunks)[:120].replace("\n", " "))
        print()
