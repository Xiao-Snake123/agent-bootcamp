"""检索层（第 7 章）：markdown 切块 + BM25 + 可选向量 + RRF 融合。

对应 content_outline.md 第 7 章锚点「retriever/indexer（升级为真实向量检索）」。
embed_fn 可选：不传即纯 BM25；传入则内置分批（DashScope 单次上限 10）。
"""
from __future__ import annotations

import glob
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from ._util import tokenize


@dataclass
class Document:
    id: str
    text: str
    source: str = ""
    title: str = ""


def chunk_markdown(text: str, source: str = "", max_chars: int = 900) -> list:
    """按 ## 小节切块，超长按句号再滑窗，保留标题前缀便于语义检索。"""
    heading = re.search(r"^#\s+(.+)$", text, re.M)
    chapter = heading.group(1).strip() if heading else Path(source).stem
    parts = re.split(r"(?m)^##\s+(.+)$", text)
    blocks = [(chapter, parts[0])]
    for i in range(1, len(parts), 2):
        blocks.append((parts[i].strip(), parts[i + 1] if i + 1 < len(parts) else ""))
    docs = []
    for title, body in blocks:
        body = body.strip()
        if not body:
            continue
        sentences = re.split(r"(?<=[。！？\n])", body)
        buf = ""
        for sentence in sentences:
            if len(buf) + len(sentence) > max_chars and buf:
                docs.append(Document(id=f"d{len(docs)}", text=f"{chapter} / {title}\n{buf}",
                                     source=source, title=title))
                buf = sentence
            else:
                buf += sentence
        if buf.strip():
            docs.append(Document(id=f"d{len(docs)}", text=f"{chapter} / {title}\n{buf}",
                                 source=source, title=title))
    return docs


class Indexer:
    """把目录里的 md 建成文档集。"""

    def __init__(self, documents: list | None = None):
        self.documents: list = list(documents or [])

    @classmethod
    def from_dir(cls, directory: str, pattern: str = "**/*.md") -> "Indexer":
        docs = []
        for fp in sorted(glob.glob(str(Path(directory) / pattern), recursive=True)):
            text = Path(fp).read_text(encoding="utf-8")
            for d in chunk_markdown(text, source=Path(fp).name):
                d.id = f"d{len(docs)}"
                docs.append(d)
        return cls(docs)

    def add_text(self, text: str, source: str = "inline"):
        self.documents.extend(chunk_markdown(text, source=source))
        for i, d in enumerate(self.documents):
            d.id = f"d{i}"
        return self


def _cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class HybridRetriever:
    """BM25 ∪ 向量，用 RRF 融合排名（第 7 章 hybrid 的最小真实实现）。"""

    def __init__(self, documents: list, embed_fn=None, k1: float = 1.5,
                 b: float = 0.75, rrf_k: int = 60):
        self.docs = documents
        self.embed_fn = embed_fn
        self.k1, self.b, self.rrf_k = k1, b, rrf_k
        self.tokens = [tokenize(d.text) for d in documents]
        self.n = len(documents)
        self.df = {}
        for toks in self.tokens:
            for word in set(toks):
                self.df[word] = self.df.get(word, 0) + 1
        self.avgdl = sum(len(t) for t in self.tokens) / max(self.n, 1)
        self.vecs = []
        if embed_fn and documents:
            for i in range(0, len(documents), 8):   # DashScope 单次批量上限
                self.vecs.extend(embed_fn([d.text for d in documents[i:i + 8]]))

    def _bm25(self, query: str, top_k: int) -> list:
        q = tokenize(query)
        ranked = []
        for i, toks in enumerate(self.tokens):
            freq = {}
            for w in toks:
                freq[w] = freq.get(w, 0) + 1
            score = 0.0
            for term in q:
                if term not in self.df or freq.get(term, 0) == 0:
                    continue
                idf = math.log(1 + (self.n - self.df[term] + 0.5) / (self.df[term] + 0.5))
                f = freq[term]
                score += idf * (f * (self.k1 + 1)) / (
                    f + self.k1 * (1 - self.b + self.b * len(toks) / self.avgdl))
            if score > 0:
                ranked.append((i, score))
        return sorted(ranked, key=lambda x: -x[1])[:top_k]

    def _vector(self, query: str, top_k: int) -> list:
        qv = self.embed_fn([query])[0]
        scored = [(_cosine(qv, v), i) for i, v in enumerate(self.vecs)]
        return [(i, s) for s, i in sorted(scored, reverse=True)[:top_k] if s > 0]

    def search(self, query: str, top_k: int = 5) -> list:
        """返回 [{'text','source','title','score'}]，按 RRF 融合分数降序。"""
        ranks = [self._bm25(query, top_k * 3)]
        if self.vecs:
            ranks.append(self._vector(query, top_k * 3))
        fused = {}
        for rank in ranks:
            for pos, (idx, _) in enumerate(rank):
                fused[idx] = fused.get(idx, 0.0) + 1.0 / (self.rrf_k + pos + 1)
        top = sorted(fused.items(), key=lambda kv: -kv[1])[:top_k]
        return [{"text": self.docs[i].text, "source": self.docs[i].source,
                 "title": self.docs[i].title, "score": round(score, 6)}
                for i, score in top]
