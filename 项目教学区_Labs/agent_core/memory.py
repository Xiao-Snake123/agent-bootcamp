"""记忆抽象层。

P0 仅提供短期 BufferMemory（最近 N 条）。K4 会在此之上加长期 VectorMemory。
接口稳定：add / get，后续替换实现不影响 Agent。
"""

from abc import ABC, abstractmethod
from collections import deque


class Memory(ABC):
    @abstractmethod
    def add(self, item):
        ...

    @abstractmethod
    def get(self, query=None, k: int = 4):
        """返回与查询相关的记忆条目（P0 忽略 query，仅按窗口返回）。"""
        ...


class BufferMemory(Memory):
    def __init__(self, window: int = 20):
        self.window = window
        self._buf = deque(maxlen=window)

    def add(self, item):
        self._buf.append(item)

    def get(self, query=None, k: int = 4):
        items = list(self._buf)
        return items[-k:] if k else items
