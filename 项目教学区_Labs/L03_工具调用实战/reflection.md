# L03 Reflection（回扣 K3）

## 1. 本 Lab 验证了 K3 的哪一点？
验证了"模型返回 tool_calls、代码执行"的工业级协议：`FunctionCallingAgent` 消费 `MockFunctionCaller` 返回的 `[{name, arguments}]`；`tools_to_openai_schema` 把 `agent_core` 的 `Tool` 描述成 OpenAI 格式，模型据此"发现"并选择工具。同一句"算 23*17 并查上海天气"在一轮里产出两个 tool_calls，印证了 K3 的"并行调用"；新增的 `get_search` 演示了第三个工具的即插即用。

## 2. 实现中踩了什么坑（对应理论"常见陷阱"）？
- **陷阱② schema 不严**：`CalculatorTool.schema` 用 `required:["expr"]` 约束必填；`test_param_validation_clean` 验证非法表达式被工具拒绝（ok=False），不进 eval。
- **陷阱④ 不校验参数就执行**：`FunctionCallingAgent` 仍走 `ToolRegistry.dispatch`（已按 schema 清洗参数），不信任模型给的 arguments。
- **陷阱⑤ tool 结果不加 name/tool_call_id**：`fc.py` 现在给每个 call 分配 `tool_call_id` 并回灌 `{"role":"tool","tool_call_id":...,"name":name}`，并行多工具时模型能一一对应（修正了旧版只用 name 的误导）。`test_tool_call_id_pairing` 验收 id 唯一非空。
- **陷阱① description 含糊**：`WeatherTool.description` 写明"参数为城市名，如：北京"，降低选错 / 填错概率。
- **陷阱⑥ 工具结果过大**：真实 search/天气可能返回长文本，回灌前需截断或摘要，否则爆窗口烧钱；本 Lab mock 数据短，未体现，但架构上 observation 应由调用方按需裁剪。
- **陷阱⑦⑨ mock 与真实 API 差异**：`MockFunctionCaller` 在 tool_calls 里塞了 `thought` 字段且未返回 `id`——这是离线简化。真实 OpenAI 模式模型不返回 `thought`，且并行必须带 `tool_call_id`；接入真 API 时这两点要改（本 Lab 的 `call_0/call_1` 已示范 id 配对）。

## 3. 若重做会改什么？
- 接真实 `OpenAIClient`，把 `tools=tool_schemas` 透传，让模型原生返回带 `id` 的 `tool_calls`；处理流式 partial（按 id 拼接 arguments）。
- 用 `tool_choice` 约束行为（如"必须先搜索"）。
- 把 `FunctionCallingAgent` 提升进 `agent_core`，作为 L1 `Agent` 的"工具调用增强版"，供 K4+ 复用。
- `_dispatch_with_retry` 预留失败重试：当前 mock 校验失败重试无效，真实 API 临时错误（超时/限流）时可救活；重试只对"已注册但执行失败"有意义。
