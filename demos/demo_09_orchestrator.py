"""第 9 章 · 编排与框架：状态图 + checkpoint 恢复 + 幂等 + HITL。

看什么：节点拓扑执行、每步写 checkpoint、重启后跳过已完成节点；
外部副作用用 once() 保证只发生一次；requires_approval 节点可人工拦截。
文档：content/核心机制篇/09_编排与框架.md
"""
from pathlib import Path

from _shared import Graph, once, run

CHECKPOINT = Path(__file__).resolve().parent / "demo09_checkpoint.json"


def build_graph() -> Graph:
    graph = Graph()

    def collect(state):
        return {"raw": [1, 2, 3]}

    def transform(state):
        return {"clean": [x * 2 for x in state["raw"]]}

    def deliver(state):
        message = once(state, "notify_user",
                       lambda: f"已通知用户：结果 {state['clean']}")
        return {"delivery": message}

    graph.add_node("collect", collect)
    graph.add_node("transform", transform)
    graph.add_node("deliver", deliver, requires_approval=True)
    graph.add_edge("collect", "transform")
    graph.add_edge("transform", "deliver")
    return graph


def body(llm, args):
    graph = build_graph()
    print("拓扑顺序:", " -> ".join(graph.order()))

    CHECKPOINT.unlink(missing_ok=True)
    first = graph.run({"goal": "处理数据并通知"},
                      checkpoint_path=str(CHECKPOINT),
                      approver=lambda name, state: True)
    print("首次运行:", first["delivery"], "| 完成节点:", first["_done"])

    resumed = graph.run(checkpoint_path=str(CHECKPOINT), resume=True,
                        approver=lambda name, state: True)
    print("恢复运行: 完成节点 =", resumed["_done"],
          "| 副作用次数 =", len(resumed["_effects"]), "（应为 1，不重复发通知）")

    denied = graph.run({}, approver=lambda name, state: False)
    print("拒绝审批: 跳过节点 =", denied["_skipped"], "| 完成节点 =", denied["_done"])

    CHECKPOINT.unlink(missing_ok=True)
    print("要点：checkpoint 必须在副作用提交之后更新；外部调用要带幂等键，"
          "否则重放会重复发消息/重复扣款。")


if __name__ == "__main__":
    run(9, "编排与框架（checkpoint / 幂等 / HITL）", body)
