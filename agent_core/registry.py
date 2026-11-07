"""能力注册表（design_docs/03 §2）：每个能力 = 一个可插拔的注册模块。"""
from __future__ import annotations


class Registry:
    def __init__(self):
        self._items: dict = {}

    def register(self, name: str, obj, replace: bool = False):
        if name in self._items and not replace:
            raise ValueError(f"能力 {name} 已注册；如需覆盖请传 replace=True")
        self._items[name] = obj
        return obj

    def get(self, name: str):
        if name not in self._items:
            raise KeyError(f"未注册的能力：{name}，可用：{self.list_names()}")
        return self._items[name]

    def list_names(self) -> list:
        return list(self._items)

    def build(self, name: str, *args, **kwargs):
        factory = self.get(name)
        return factory(*args, **kwargs) if callable(factory) else factory
