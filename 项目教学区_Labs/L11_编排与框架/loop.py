"""L11 演示：用图编排把 Planner→Executor→Critic→人工审批 串成流水线。

运行：
    cd 项目教学区_Labs/L11_编排与框架
    python loop.py

节点内部用 Mock 逻辑，便于离线跑；README 写明每个节点可替换为 K3–K10 真实模块
（planner→K5 Planner、executor→K3/K9 工具执行、critic→K6 Reflector、人工→护栏）。
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from orchestrator import Graph, Node, GraphState, END

_side_effects = {"executor_runs": 0}   # 演示幂等：副作用计数（如"真正调用了工具几次"）


def planner(d):
    d["plan"] = ["查资料", "写草稿", "复核"]


def executor(d):
    _side_effects["executor_runs"] += 1   # 副作用：真实场景可能是发请求/扣款
    d["executed"] = d["plan"]


def critic(d):
    d["critic_ok"] = False                # 故意判"需人工复核"
    d["__next__"] = "human_approve" if not d["critic_ok"] else END


def human_approve(d):
    d["approved"] = d.get("__human_approved__", False)


def build_graph():
    g = Graph(start="planner")
    g.add(Node("planner", planner, next="executor"))
    g.add(Node("executor", executor, next="critic"))
    g.add(Node("critic", critic, next=None))            # 条件边由 __next__ 决定
    g.add(Node("human_approve", human_approve, next=END, human=True))
    return g


def demo():
    g = build_graph()
    cp = os.path.join(_HERE, "_checkpoint.json")
    if os.path.exists(cp):
        os.remove(cp)

    # ① 首次运行：跑到人工节点暂停（模拟进程中断 / 需人工）
    state, status = g.run(checkpoint=cp)
    print("① 首次运行:", status, "| 已执行:", state.done,
          "| 副作用(执行次数):", _side_effects["executor_runs"])
    print("   需人工节点:", state.data.get("__need_human__"))

    # ② 人工批准并恢复（从 checkpoint 断点续跑，已完成节点不重跑）
    state2, status2 = g.run(state=state, checkpoint=cp,
                            human_input={"__human_approved__": True})
    print("② 恢复运行:", status2, "| 已执行:", state2.done,
          "| 副作用(执行次数):", _side_effects["executor_runs"])
    print("   审批结果:", state2.data.get("approved"))

    # ③ 幂等验证：再 resume（未批准）时，已完成节点不会重复执行副作用
    before = _side_effects["executor_runs"]
    state3, status3 = g.run(state=GraphState(current="planner",
                            data={"plan": ["x"]}, done=["planner", "executor"]),
                            checkpoint=cp)
    print("③ 幂等续跑:", status3, "| 副作用增量:",
          _side_effects["executor_runs"] - before, "(应为 0)")


if __name__ == "__main__":
    demo()
