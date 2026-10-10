# L02 Reflection（回扣 K2）

## 1. 本 Lab 验证了 K2 的哪一点？
验证了"提示是驱动 LLM 的唯一旋钮"：`PromptBuilder` 把 system / few-shot / structured-output 组装成 messages，`DemoLLM` 在收到"只输出 JSON"的系统提示时吐 JSON、否则吐自然语言——同一句用户输入，输出形态完全由提示决定。同时印证了"结构化输出对 Agent 至关重要"：L1 的 `Agent` 正是靠解析模型 JSON 决策（`_parse`）才能跑通循环。

## 2. 实现中踩了什么坑（对应理论"常见陷阱"）？
- **陷阱④ 不要求结构化输出**：早期若让模型自由发挥，L1 的 `_parse` 会失败、循环崩。我们用 `with_structured_output` 把"只输出 JSON + schema"写进 system，降低解析失败率。
- **陷阱① 忽视上下文窗口**：`truncate_to_tokens` 演示了超长文本必须截断；真实应用应接 tokenizer（如 tiktoken）而非字数近似。
- **陷阱⑤ prompt 里算数**：`DemoLLM` 不做任何计算，算数仍交 L1 的 `CalculatorTool`，提示只负责"指挥"。

## 3. 若重做会改什么？
- 用真实 tokenizer（tiktoken）替换 `truncate_to_tokens` 的字数近似，精确对齐 token 上限。
- 把 `with_structured_output` 升级为 K3 的 Function Calling（模型返回 `tool_calls` 而非裸 JSON）。
- 给 `PromptBuilder` 增加"模板变量渲染"（Jinja 风格），方便后续 Lab 复用同一套骨架。
