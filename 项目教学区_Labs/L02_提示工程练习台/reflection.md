# L02 Reflection（回扣 K2）

## 1. 本 Lab 验证了 K2 的哪一点？
验证了"提示是驱动 LLM 的唯一旋钮"：`PromptBuilder` 把 system / few-shot / structured-output 组装成 messages，`DemoLLM` 在收到"只输出 JSON"的系统提示时吐 JSON、否则吐自然语言——同一句用户输入，输出形态完全由提示决定。同时印证了"结构化输出对 Agent 至关重要"：L1 的 `Agent` 正是靠解析模型 JSON 决策（`_parse`）才能跑通循环。

## 2. 技能演练说明了什么（K2 第四节方法）
`challenge.py` 把"口语→订餐 JSON"变成可运行对照：`BAD_SYSTEM`（"你帮用户处理订单。"）下 `ChallengeLLM` 回自由文本"好的，我已经记下您的请求。"；`REFERENCE_GOOD`（按模板写了角色/任务/枚举/约束/示例）下回 `{"intent":"cancel","items":[]}`。**差异全在提示写法**——证明 K2 教的"模板 + 配方"不是空话，写得好不好直接决定模型产出可否被代码解析。这是"会用 PromptBuilder 组装"与"会写提示内容"的关键分界。

## 3. 实现中踩了什么坑（对应理论"常见陷阱"）？
- **陷阱④ 不要求结构化输出**：早期若让模型自由发挥，L1 的 `_parse` 会失败、循环崩。我们用 `with_structured_output` 把"只输出 JSON + schema"写进 system，降低解析失败率。
- **陷阱① 忽视上下文窗口 / lost-in-the-middle**：`truncate_to_tokens` 演示了超长文本必须截断；真实应用应接 tokenizer（如 tiktoken）。
- **陷阱⑤ prompt 里算数**：`DemoLLM` 不做任何计算，算数仍交 L1 的 `CalculatorTool`，提示只负责"指挥"。
- **前沿点·prompt caching（已落成可运行估算）**：`prompt.py` 新增 `estimate_cache_savings`，离线演示"稳定 system 被缓存后，多轮对话只在第一次计 system 的 token"。真实 API 里这笔账体现为 `cache_creation`/`cache_read` 两类低价 token——Agent 每轮重发 system，命中缓存后成本可降数倍。这是 K02 强调的"成本护栏"在提示层的具体抓手。
- **真实 token 截断**：`truncate_to_tokens` 改用 tiktoken 精确计数（不可用时退化为字数近似）。中文一个字常占 1–2 token，纯字数近似会低估、导致长中文文本悄悄超出窗口——这正是 K2 "lost-in-the-middle" 风险的前端防线。

## 4. 若重做会改什么？
- 用真实 tokenizer（tiktoken）替换 `truncate_to_tokens` 的字数近似，精确对齐 token 上限。
- 把 `with_structured_output` 升级为 K3 的 Function Calling（模型返回 `tool_calls` 而非裸 JSON）；用 native structured outputs 强制 schema。
- 把 `challenge.py` 的 `YOUR_SYSTEM` 接入真实 `OpenAIClient`，让学员在真模型上对比 BAD / GOOD 的 JSON 质量（离线 Mock 仅演示行为分叉）。
