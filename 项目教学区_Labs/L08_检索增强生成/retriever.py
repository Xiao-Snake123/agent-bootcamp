"""L08 检索：用 BM25 近似打分做离线 top-k 召回（真实应为 embedding + 向量库 + hybrid）。

中文按字、英文按词切 token，用交集大小近似相关性打分——离线即可演示
"检索注入"机制；技能演练可替换为 sentence-transformers + Qdrant 的真实向量检索。
"""

import re

from indexer import Indexer

_TOKEN_RE = re.compile(r"[一-鿿]|[a-zA-Z0-9]+")


def _tokens(text: str):
    return set(_TOKEN_RE.findall(text.lower()))


class Retriever:
    def __init__(self, indexer: Indexer):
        self.indexer = indexer

    def retrieve(self, query: str, k: int = 3):
        q_tokens = _tokens(query)
        if not q_tokens:
            return []
        scored = []
        for ch in self.indexer.chunks:
            overlap = len(q_tokens & _tokens(ch["text"]))
            if overlap:
                scored.append((overlap, ch))
        scored.sort(key=lambda x: -x[0])
        return [ch for _, ch in scored[:k]]
