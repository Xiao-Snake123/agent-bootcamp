"""L11 最小图编排器：声明式节点 + 条件边 + checkpoint 恢复 + 人工回环 + 幂等。

对应 K11：把 K3–K10 的模块作为节点串成流水线；状态持久化以便断点续跑；
human-in-the-loop 在人工节点暂停；幂等避免重跑重复副作用。
（这是 LangGraph 的极简内核映射，design_docs 要求 K11 前不引入重框架。）
"""

import json
import os
from dataclasses import dataclass, field

END = "__END__"


class Node:
    def __init__(self, name, run, next=None, human=False):
        self.name = name
        self.run = run          # Callable[[dict], None] 原地修改 state["data"]
        self.next = next        # 固定下一节点名；None 时由 data["__next__"] 决定（条件边）
        self.human = human      # 是否人工节点（暂停等输入）


@dataclass
class GraphState:
    data: dict = field(default_factory=dict)
    current: str = ""
    done: list = field(default_factory=list)   # 已执行节点（幂等记录）


class Graph:
    def __init__(self, start):
        self.nodes = {}
        self.start = start

    def add(self, node: Node):
        self.nodes[node.name] = node

    def save_checkpoint(self, state: GraphState, path):
        snap = {"current": state.current, "data": state.data, "done": state.done}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=2)

    def load_checkpoint(self, path) -> GraphState:
        with open(path, encoding="utf-8") as f:
            snap = json.load(f)
        return GraphState(data=snap["data"], current=snap["current"], done=snap["done"])

    def run(self, state: GraphState = None, checkpoint: str = None, human_input: dict = None):
        """执行图。返回 (GraphState, status)。

        status: "DONE" 跑完；"PAUSED_FOR_HUMAN" 在人工节点暂停（已落 checkpoint）。
        human_input: 恢复时注入的人工决策（如 {"__human_approved__": True}）。
        """
        if state is None:
            state = GraphState(current=self.start)
        if human_input is not None:
            state.data.update(human_input)

        while state.current != END and state.current in self.nodes:
            node = self.nodes[state.current]
            # 人工回环：需外部输入且尚未批准 → 暂停（先落 checkpoint 以便恢复）
            if node.human and not state.data.get("__human_approved__"):
                state.data["__need_human__"] = node.name
                if checkpoint:
                    self.save_checkpoint(state, checkpoint)
                return state, "PAUSED_FOR_HUMAN"
            # 幂等：已执行的节点跳过副作用，仅沿边前进（防恢复/重跑重复副作用）
            if node.name in state.done:
                state.current = node.next or state.data.get("__next__", END)
                continue
            node.run(state.data)                 # 执行节点（原地改 data）
            state.done.append(node.name)
            if checkpoint:
                self.save_checkpoint(state, checkpoint)
            state.current = node.next or state.data.get("__next__", END)
        return state, "DONE"
