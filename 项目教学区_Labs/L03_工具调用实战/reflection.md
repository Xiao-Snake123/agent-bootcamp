# L03 Reflection（回扣 K3）

## 1. 本 Lab 验证了 K3 的哪一点？
验证了"模型返回 tool_calls、代码执行"的工业级协议：`FunctionCallingAgent` 不再解析 L1 的手写 `{action:...}` JSON，而是消费 `MockFunctionCaller` 返回的 `[{name, arguments}]`；`tools_to_openai_schema` 把 `agent_core` 的 `Tool` 描述成 OpenAI 格式，模型据此"发现"并选择工具。同一句"算 23*17 并查上海天气"在一轮里产出两个 tool_calls，印证了 K3 的"并行调用"。

## 2. 实现中踩了什么坑（对应理论"常见陷阱"）？
- **陷阱② schema 不严**：`CalculatorTool.schema` 用 `required:["expr"]` 约束必填；`test_param_validation_clean` 验证非法表达式被工具拒绝（ok=False），不进 eval。
- **陷阱④ 不校验参数就执行**：`FunctionCallingAgent` 仍走 `ToolRegistry.dispatch`（已按 schema 清洗参数），不信任模型给的 arguments。
- **陷阱⑤ tool 结果不加 name**：dispatch 后 `messages.append({"role":"tool","content":...,"name":name})`，并行多工具时模型能对应到正确调用。
- **陷阱① description 含糊**：`WeatherTool.description` 写明"参数为城市名，如：北京"，降低模型选错 / 填错概率。

## 3. 若重做会改什么？
- 接真实 `OpenAIClient`，把 `tools=tool_schemas` 透传给 API，让模型原生返回 `tool_calls`（而非 Mock）。
- 支持"串行多轮"：让模型一轮只返回一个有依赖的 tool_call，结果回灌后再决定下一步（当前 Mock 已能并行，串行只需模型行为变化）。
- 把 `FunctionCallingAgent` 提升进 `agent_core`，作为 L1 `Agent` 的"工具调用增强版"，供 K4+ 复用。
