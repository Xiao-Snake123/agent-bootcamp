"""L08 索引：把文档切成 chunk 并建立内存库（离线替代"切片→嵌入→入库"）。

真实 RAG 这里应：切片 → embedding → 存入向量库（Qdrant 等）。本 Lab 用
内存 chunk 列表离线近似，结构等价；技能演练可换成真 embedding + 向量库。
"""

import re


class Indexer:
    def __init__(self):
        self.chunks = []   # list of {"id", "text", "source"}

    def _split(self, text: str):
        """按句切分并过滤过短片段（离线 chunk 策略近似）。"""
        for sent in re.split(r"(?<=[。.!?])", text):
            sent = sent.strip()
            if len(sent) >= 4:
                yield sent

    def build(self, docs):
        """docs: list of (source_name, text)。返回建立的 chunk 数。"""
        cid = 0
        for source, text in docs:
            for sent in self._split(text):
                self.chunks.append({"id": cid, "text": sent, "source": source})
                cid += 1
        return len(self.chunks)
