"""验证向量检索（Qdrant / 内存降级）是否可用：强制 hybrid 初始化并查询。"""
import rag_server as r

# 若当前 RETRIEVER 非 vector/hybrid，强制初始化向量以测试
if r.RETRIEVER not in ("vector", "hybrid"):
    r.RETRIEVER = "hybrid"
    r._init_vectors()

print("RETRIEVER =", r.RETRIEVER, "| vector_mode =", r._qdrant_mode)
print("DASHSCOPE embed =", bool(r.EMBED_KEY))
if not r.EMBED_KEY:
    print("无 DASHSCOPE_API_KEY，无法测试向量")
else:
    for q in ["多 Agent 什么时候该用，和单 Agent 加工具的区别？",
              "上下文工程里 KV 缓存为什么重要？",
              "生产化里语义缓存怎么提升命中？"]:
        print("\nQ:", q)
        for c in r.retrieve(q, 5):
            print("  -", c["chapter"], "/", c["section"])
