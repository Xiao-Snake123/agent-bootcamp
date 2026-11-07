"""第 2 章 · 工具系统：JSON Schema、并行 tool_calls、参数校验与错误回填。

看什么：一次响应里多个 tool_calls 如何并行分发；缺必填参数时返回 ok=False
观察而不是抛异常中断，让模型自己纠正。
文档：content/核心机制篇/02_工具系统.md
"""
from _shared import (Agent, ToolRegistry, make_tool, run, safe_calc,
                     show_trajectory)


def build_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(make_tool(
        "calculator", "计算四则运算表达式",
        {"type": "object", "properties": {"expr": {"type": "string"}}, "required": ["expr"]},
        lambda expr: safe_calc(expr)))
    reg.register(make_tool(
        "word_count", "统计文本词数（按空白切分）",
        {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        lambda text: len(text.split())))
    return reg


def body(llm, args):
    reg = build_registry()
    for schema in reg.openai_schemas():
        print("  tools schema:", schema["function"]["name"],
              "required =", schema["function"]["parameters"].get("required"))
    agent = Agent(llm, reg,
                  system="可同时调用多个工具；参数必须严格符合 schema；拿到全部结果后总结。")
    answer, traj = agent.run(
        args.goal or "请同时统计 'agent core loop' 的词数并计算 7*6，然后汇总", max_steps=5)
    print("最终答案:", answer)
    show_trajectory(traj)

    # 单独演示参数校验：缺少必填参数应返回 ok=False，而不是让整个循环崩溃
    bad = reg.dispatch("calculator", {})
    print("参数校验（故意缺 expr）:", bad.content, "| ok =", bad.ok)


if __name__ == "__main__":
    script = [{"content": "", "tool_calls": [
        {"name": "word_count", "arguments": {"text": "agent core loop"}},
        {"name": "calculator", "arguments": {"expr": "7*6"}},
    ]}]
    run(2, "工具系统（Schema / 并行调用 / 校验）", body, script=script)
