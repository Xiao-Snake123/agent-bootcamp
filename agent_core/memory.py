"""记忆层（v2）：接口稳定，压缩与召回升级为真实实现。

- BufferMemory    : 滑动窗口（v1 保留）
- SummaryMemory   : 超窗时用 LLM 真正生成摘要（v1 的拼接近似被替换）
- LongTermMemory  : 命名空间隔离 + 可插拔 retriever（子串回退）
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque


class Memory(ABC):
    @abstractmethod
    def add(self, item): ...

    @abstractmethod
    def get(self, query=None, k: int = 4): ...

    def clear(self):
        raise NotImplementedError


class BufferMemory(Memory):
    """短期工作记忆：最近 keep 条原样保留，超 window 折叠成一条摘要句。"""

    def __init__(self, window: int = 20, keep: int = 4):
        self.window, self.keep = window, keep
        self._buf = deque()

    def add(self, item):
        self._buf.append(str(item))
        if len(self._buf) > self.window:
            old = list(self._buf)[:-self.keep]
            self._buf = deque(["[历史摘要] " + " | ".join(old)]
                              + list(self._buf)[-self.keep:])

    def get(self, query=None, k: int = 4):
        items = list(self._buf)
        return items[-k:] if k else items

    def clear(self):
        self._buf.clear()


class SummaryMemory(Memory):
    """真摘要压缩：超窗时调 LLM 生成摘要，而非拼接（对应第 3 章 compaction）。"""

    def __init__(self, llm, window: int = 8, keep: int = 4):
        self.llm, self.window, self.keep = llm, window, keep
        self._buf = deque()

    def add(self, item):
        self._buf.append(str(item))
        if len(self._buf) > self.window:
            old = list(self._buf)[:-self.keep]
            prompt = ("把以下 Agent 历史步骤压缩成 2 句以内的中文摘要，"
                      "保留关键结论与数字，不要复述原文：\n" + "\n".join(old))
            try:
                summary = "[LLM 摘要] " + self.llm.complete(
                    [{"role": "user", "content": prompt}])
            except Exception as e:
                summary = f"[压缩失败，保留条数] {e}"
            self._buf = deque([summary] + list(self._buf)[-self.keep:])

    def get(self, query=None, k: int = 4):
        items = list(self._buf)
        return items[-k:] if k else items

    def clear(self):
        self._buf.clear()


class LongTermMemory(Memory):
    """跨会话长期记忆：显式 save_fact，按 namespace 隔离，可注入检索器。"""

    def __init__(self, namespace: str = "default", retriever=None):
        self.namespace = namespace
        self.retriever = retriever
        self._store: dict[str, str] = {}

    def save_fact(self, key: str, value: str):
        self._store[key] = value

    def recall(self, query: str) -> str:
        if query in self._store:
            return self._store[query]
        if self.retriever is not None:
            hits = self.retriever.search(query, top_k=1)
            return hits[0] if hits else ""
        for key, value in self._store.items():
            if query in key or key in query:  # 子串回退（无向量库时）
                return value
        return ""

    def add(self, item):
        """长期写入应由 Agent 显式 save_fact，不自动灌入每步观察（避免噪声）。"""
        return

    def get(self, query=None, k: int = 4):
        if query is None:
            return list(self._store.items())[-k:]
        val = self.recall(str(query))
        return [val] if val else []

    def clear(self):
        self._store.clear()
