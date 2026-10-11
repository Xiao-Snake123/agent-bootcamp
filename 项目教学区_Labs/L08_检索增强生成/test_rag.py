"""L08 验收：切片建库、检索相关性、生成含出处标注。"""

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


def _build():
    docs = [
        ("制度.txt", "年假规定：入职满一年享5天年假。病假需提供医院证明。"),
        ("手册.txt", "RAG 用于外部知识问答，需标注出处。"),
    ]
    idx = Indexer()
    idx.build(docs)
    return idx


def test_indexer_build_creates_chunks():
    idx = _build()
    assert len(idx.chunks) >= 2


def test_retriever_returns_relevant_chunk():
    idx = _build()
    hits = Retriever(idx).retrieve("年假怎么算", k=2)
    assert hits
    assert any("年假" in h["text"] for h in hits)


def test_generator_cites_source():
    idx = _build()
    hits = Retriever(idx).retrieve("年假", k=1)
    out = Generator().generate("年假几天", hits)
    assert "[" in out and "]" in out          # 出处标注
    assert hits[0]["text"] in out             # 检索内容被注入
