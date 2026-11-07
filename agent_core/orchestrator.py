"""编排与框架（第 9 章）：有向状态图 + checkpoint + 幂等 + HITL。

对应 content_outline.md 第 9 章锚点「agent_core/orchestrator.py（新增）」。
不依赖 LangGraph，用最小拓扑调度把「可恢复 / 不重复副作用」讲清楚。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Node:
    name: str
    fn: object
    requires_approval: bool = False


def once(state: dict, key: str, fn):
    """幂等副作用：同一个 key 在整条轨迹里只真正执行一次（重启恢复也跳过）。"""
    effects = state.setdefault("_effects", [])
    if key in effects:
        return state.get(f"effect:{key}")
    value = fn()
    effects.append(key)
    state[f"effect:{key}"] = value
    return value


class Graph:
    """节点=状态，边=转移；每步后写 checkpoint，重启可按 _done 恢复。"""

    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, list] = {}

    def add_node(self, name: str, fn, requires_approval: bool = False):
        self.nodes[name] = Node(name, fn, requires_approval)
        self.edges.setdefault(name, [])
        return self

    def add_edge(self, src: str, dst: str):
        self.edges.setdefault(src, []).append(dst)
        self.edges.setdefault(dst, [])
        return self

    def order(self) -> list:
        """Kahn 拓扑排序；有环时把剩余节点追加，返回顺序仍可执行。"""
        indeg = {name: 0 for name in self.nodes}
        for src, dsts in self.edges.items():
            for dst in dsts:
                if dst in indeg:
                    indeg[dst] += 1
        queue = [n for n, d in indeg.items() if d == 0]
        result = []
        while queue:
            node = queue.pop(0)
            result.append(node)
            for dst in self.edges.get(node, []):
                if dst in indeg:
                    indeg[dst] -= 1
                    if indeg[dst] == 0:
                        queue.append(dst)
        result.extend(n for n in self.nodes if n not in result)
        return result

    def run(self, state: dict | None = None, checkpoint_path: str | None = None,
            approver=None, resume: bool = False) -> dict:
        """approver(name, state) -> bool；默认 None 表示自动批准（离线友好）。"""
        path = Path(checkpoint_path) if checkpoint_path else None
        if resume and path and path.exists():
            state = json.loads(path.read_text(encoding="utf-8"))
        state = dict(state or {})
        state.setdefault("_done", [])
        state.setdefault("_effects", [])
        state.setdefault("_skipped", [])

        for name in self.order():
            if name in state["_done"]:      # 幂等：恢复时跳过已完成节点
                continue
            node = self.nodes[name]
            if node.requires_approval and approver is not None and not approver(name, state):
                state["_skipped"].append(name)
                continue
            result = node.fn(state)
            if isinstance(result, dict):
                state.update(result)
            if name not in state["_done"]:
                state["_done"].append(name)
            if path:
                path.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        return state
