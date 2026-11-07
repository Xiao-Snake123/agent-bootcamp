"""第 4 章 · 规划与分解：Plan-and-Execute + 依赖 DAG + 失败重规划。

看什么：LLM 产出带 depends_on 的计划；Planner 按拓扑序调度；
某步失败时保留已完成步骤、只重规划剩余部分。
文档：content/核心机制篇/04_规划与分解.md
"""
from _shared import Planner, run

OFFLINE_PLAN = ('['
                '{"id":"s1","description":"确定调研范围与验收标准","depends_on":[]},'
                '{"id":"s2","description":"收集三个来源的资料","depends_on":["s1"]},'
                '{"id":"s3","description":"交叉验证并汇总结论","depends_on":["s1","s2"]}'
                ']')


def body(llm, args):
    goal = args.goal or "写一份关于 Agent 评测方法的简短调研报告"
    planner = Planner(llm)
    plan = planner.make_plan(goal, max_steps=4)
    print("初始计划:")
    print(plan.summary())

    order = []

    def run_step(step):
        order.append(step.id)
        return f"完成 {step.description}（产出已记录）"

    plan = planner.execute(plan, run_step, max_replans=1)
    print("\n执行顺序（应满足依赖）:", " -> ".join(order))
    print("最终状态:")
    print(plan.summary())
    print("已完成:", len(plan.done), "| 失败:", len(plan.failed))
    print("要点：重规划保留已完成输出，避免整体重来；max_replans 限制防止无限重规划。")


if __name__ == "__main__":
    run(4, "规划与分解（DAG / 重规划）", body, script=[OFFLINE_PLAN])
