"""第 1 章 · 推理-行动循环（原生 Function Calling 版）。

看什么：assistant(tool_calls) → tool(tool_call_id) → assistant 的标准协议回注，
以及 max_steps / 重复调用检测 / 成本护栏三道防线。
文档：content/核心机制篇/01_推理-行动循环ReAct.md
"""
from _shared import (Agent, ToolRegistry, make_tool, run, safe_calc,
                     show_trajectory, tool_call)

CALC_SCHEMA = {"type": "object",
               "properties": {"expr": {"type": "string", "description": "四则表达式，如 12*8"}},
               "required": ["expr"]}


def body(llm, args):
    registry = ToolRegistry()
    registry.register(make_tool("calculator", "计算四则运算表达式",
                                CALC_SCHEMA, lambda expr: safe_calc(expr)))
    print("工具 schema:", registry.openai_schemas()[0]["function"]["parameters"])
    agent = Agent(llm, registry,
                  system="需要计算时必须调用 calculator 工具，拿到结果后用一句话给出结论。",
                  loop_limit=2)
    answer, traj = agent.run(args.goal or "请算 12*8 等于多少", max_steps=5)
    print("最终答案:", answer)
    show_trajectory(traj)
    if traj.steps:
        print("协议回注示例:")
        print(f"  assistant.tool_calls[0].id = {traj.steps[0].tool_call_id}")
        print(f"  tool.tool_call_id          = {traj.steps[0].tool_call_id}  (必须一致，否则 API 400)")


if __name__ == "__main__":
    run(1, "推理-行动循环 ReAct（原生 FC）", body,
        script=[tool_call("calculator", expr="12*8")])
