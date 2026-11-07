"""第 5 章 · 反思与自修正（Reflexion）：轨迹复盘 → 经验注入 → 重试。

看什么：第一轮工具失败（除零），Reflector 基于客观轨迹给出 lesson，
第二轮把 lesson 注入目标后改用正确参数；should_retry 与 max_retries 防无限循环。
文档：content/核心机制篇/05_反思与自修正.md
"""
from _shared import (Agent, Reflector, ToolRegistry, make_tool, run,
                     safe_calc, show_trajectory, tool_call)

SCHEMA = {"type": "object", "properties": {"expr": {"type": "string"}},
          "required": ["expr"]}


def body(llm, args):
    reg = ToolRegistry()
    reg.register(make_tool("calculator", "计算四则表达式", SCHEMA,
                           lambda expr: safe_calc(expr)))
    agent = Agent(llm, reg, system="需要计算时调用 calculator；失败时换一个表达式重试。")
    reflector = Reflector(llm, max_retries=1)
    goal = args.goal or "计算 100 除以 0，若不可行请给出替代计算并说明原因"

    answer, traj, reflections = reflector.run(agent, goal, max_steps=4)
    print("最终答案:", answer)
    show_trajectory(traj)
    print("\n反思记录:")
    for i, r in enumerate(reflections, 1):
        print(f"  {i}. should_retry={r.should_retry} | critique={r.critique[:80]} "
              f"| lesson={r.lesson[:80]}")
    print("要点：反思必须锚定客观反馈（工具 ok=False / 轨迹），否则会变成自我安慰式空转。")


if __name__ == "__main__":
    # 按真实调用顺序编排：agent(r1) → reflect(r1) → agent(r2) → reflect(r2)
    script = [
        tool_call("calculator", expr="100/0"),
        "除零失败，需要改用非零除数重试。",
        '{"critique":"除零导致工具失败","lesson":"改为除以非零数，例如 100/4",'
        '"should_retry":true}',
        tool_call("calculator", expr="100/4"),
        "结果 25；除零不可行时应改用等价的非零除数。",
        '{"critique":"已成功","lesson":"","should_retry":false}',
    ]
    run(5, "反思与自修正（Reflexion）", body, script=script)
