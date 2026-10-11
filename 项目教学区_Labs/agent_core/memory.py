"""记忆抽象层（K4 升级）。

分层：
- Memory(ABC)：统一接口 add / get，稳定不变；
- BufferMemory：短期工作记忆，超阈值自动 compaction（折叠旧片段为摘要），
  对应 K2 lost-in-the-middle 的前端防线；
- LongTermMemory：跨会话长期记忆，事实/语义 KV 库 + 离线语义召回近似，
  是 agentic memory 的最小可用实现（真实用 embedding + 向量库）。

设计原则见 design_docs/03 §2：接口稳定、模块可插拔、本地优先（无 Key 可跑）。
"""

from abc import ABC, abstractmethod
from collections import deque


class Memory(ABC):
    @abstractmethod
    def add(self, item):
        ...

    @abstractmethod
    def get(self, query=None, k: int = 4):
        """返回与查询相关的记忆条目；P0 的 BufferMemory 忽略 query 按窗口返回。"""
        ...


class BufferMemory(Memory):
    """短期工作记忆：滑动窗口 + 自动压缩（compaction）。

    - 最近 `keep` 条原样保留；超过 `window` 时，旧片段折叠成一条摘要句，
      避免无限累积触发 lost-in-the-middle（K2）与成本飙升。
    - 真实 compaction 应由小模型生成摘要；此处用离线拼接近似，结构等价。
    """

    def __init__(self, window: int = 20, keep: int = 4):
        self.window = window
        self.keep = keep
        self._buf = deque()

    def add(self, item):
        self._buf.append(item)
        self._maybe_compress()

    def _maybe_compress(self):
        if len(self._buf) > self.window:
            old = [str(x) for x in list(self._buf)[:-self.keep]]
            summary = "[历史摘要] " + " | ".join(old)
            self._buf = deque([summary] + list(self._buf[-self.keep:]))

    def compress(self):
        """显式触发一次压缩（即便未超 window，便于教学演示）。"""
        old = [str(x) for x in self._buf] or ["（空）"]
        summary = "[历史摘要] " + " | ".join(old)
        self._buf = deque([summary])

    def get(self, query=None, k: int = 4):
        items = list(self._buf)
        return items[-k:] if k else items


class LongTermMemory(Memory):
    """长期记忆：跨会话持久的事实/语义库（agentic memory 最小实现）。

    - 真实用 embedding + 向量库做语义召回；本教学离线用"精确匹配 + 子串回退"
      近似语义检索，结构等价（key 即语义索引）。
    - save_fact / recall 是 Agent 工具（L4 的 SaveFact/Recall）直接调用的便捷接口。
    - namespace 用于按用户/会话隔离，避免跨会话污染（陷阱⑥）。
    """

    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self._store: dict = {}

    def save_fact(self, key: str, value: str):
        self._store[key] = value

    def recall(self, query: str) -> str:
        if query in self._store:
            return self._store[query]
        for k, v in self._store.items():
            if query in k or k in query:   # 子串回退，近似语义召回
                return v
        return ""

    def add(self, item):
        """兼容 Agent.run 的 memory.add(step) 钩子。

        长期写入应由 agentic 决策（save_fact）显式完成，这里不自动写，
        避免把每步观察无差别灌进长期记忆（陷阱③噪声淹没）。
        """
        return

    def get(self, query=None, k: int = 4):
        if query is None:
            return list(self._store.items())
        val = self.recall(query)
        return [val] if val else []
