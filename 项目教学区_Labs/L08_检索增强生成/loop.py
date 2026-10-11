"""L08 演示：切片 → BM25 近似检索 top-k → 拼接生成 + 标注出处（离线，无需 Key）。

运行：
    cd 项目教学区_Labs/L08_检索增强生成
    python loop.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from indexer import Indexer
from retriever import Retriever
from generator import Generator


def demo():
    print("=== RAG 全流程（离线 BM25 近似检索）===")
    docs = [
        ("公司制度.txt", "年假规定：入职满一年享5天年假。病假需提供医院证明。"),
        ("产品手册.txt", "Agent Bootcamp 教学覆盖 K1 到 K11。RAG 用于外部知识问答。"),
        ("安全规范.txt", "密码长度至少12位，禁止重复使用历史密码。数据需加密存储。"),
    ]
    indexer = Indexer()
    n = indexer.build(docs)
    print(f"  建库 chunk 数: {n}")

    retriever = Retriever(indexer)
    question = "年假怎么算"
    hits = retriever.retrieve(question, k=2)
    print(f"  检索到 {len(hits)} 个相关片段:")
    for h in hits:
        print(f"    [{h['id']}:{h['source']}] {h['text']}")

    answer = Generator().generate(question, hits)
    print("\n  生成答案（带出处）:")
    print("  " + answer.replace("\n", "\n  "))


if __name__ == "__main__":
    demo()
