"""真实链路测试：加载 .env 的 DeepSeek + DashScope，跑通检索与生成。"""
import os
import rag_server as r

print("RETRIEVER        =", r.RETRIEVER)
print("DASHSCOPE embed  =", bool(r.EMBED_KEY))
print("DEEPSEEK key     =", bool(os.getenv("DEEPSEEK_API_KEY")))
print("(启动期应已打印 embedding 预计算 [ok]/[warn])\n")

qs = [
    "Agent 如何防止死循环和无限调用工具？",
    "RAG 为什么需要 rerank，hybrid 检索有什么好处？",
]
for q in qs:
    print("="*60)
    print("Q:", q)
    chunks = r.retrieve(q, 5)
    for c in chunks:
        print("  -", c["chapter"], "/", c["section"])
    try:
        ans = r.generate(q, chunks)
        print("A:", ans[:400].replace("\n", " "))
        print("  >> 演示模式?", "演示模式" in ans)
    except Exception as e:
        print("  !! generate ERROR:", repr(e))
