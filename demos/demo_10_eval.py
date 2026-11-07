"""第 10 章 · 评测与可观测：基于 Trajectory 的可解释评测。

看什么：不只判最终答案，还检查终止原因、失败工具调用、禁用工具、步数效率。
文档：content/核心机制篇/10_评测与可观测.md
"""
from _shared import (Agent, EvalCase, TrajectoryEvaluator, ToolRegistry,
                     make_tool, run, safe_calc, show_trajectory)

SCHEMA = {"type": "object", "properties": {"expr": {"type": "string"}},
          "required": ["expr"]}


def body(llm, args):
    registry = ToolRegistry()
    registry.register(make_tool("calculator", "计算四则表达式", SCHEMA,
                               lambda expr: safe_calc(expr)))
    agent = Agent(llm, registry, system="需要计算时调用 calculator，拿到结果后直接回答。")

    cases = [
        EvalCase(goal="请算 3*7 等于多少", keywords=["21"], max_steps=5),
        EvalCase(goal="请算 10+5 等于多少", keywords=["15"],
                 forbidden_tools=["shell"], max_steps=5),
    ]
    evaluator = TrajectoryEvaluator()
    results = evaluator.run_suite(cases, agent, max_steps=5)
    print(evaluator.report(results))
    for r in results:
        print(f"  {r.goal[:24]} -> checks={r.checks}")
    print("要点：线上还要做轨迹回放 + 用户反馈埋点；测试集全过不代表线上不崩。")


if __name__ == "__main__":
    run(10, "评测与可观测（Trajectory 评测）", body)
