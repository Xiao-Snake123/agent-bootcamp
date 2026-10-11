# L01 Reflection（回扣 K1）

## 1. 本 Lab 验证了 K1 的哪一点？
验证了"Agent = 闭环而非一次函数调用"：`Agent.run` 用 `for` 循环反复让模型决策、执行工具、回收观察，直到产出最终答案。同时印证了 Agent Loop 四环节（思考/行动/观察/终止），以及"模型只出决策、代码出结果"的边界——`MockLLMClient` 只返回 `{action:...}` 或 `{final_answer:...}`，真正的计算由 `CalculatorTool` 完成。

## 2. 实现中踩了什么坑（对应理论"常见陷阱"）？
- **陷阱② 工具结果不回灌**：最初若不分发结果、不把 `role=tool` 消息加回 `messages`，模型第二轮就看不到上一步结果。修复：dispatch 后 `messages.append({"role": "tool", ...})`。
- **陷阱③ 没有终止条件**：Mock 决策器若每次都返回 action 会无限循环。靠"已有观察就给最终答案"的策略 + `max_steps` 双保险终止。
- **陷阱④ 让模型直接出结果**：我们坚持模型只输出决策 JSON，执行与求值由代码负责，避免任意代码执行风险（计算器用白名单正则 + 禁用 `__builtins__`）。

## 3. 真实 API 与 Mock 的差异 / 成本护栏（前沿视角）
- **Mock 只是"决策器替身"**：`MockLLMClient` 按字符串规则硬编码返回 JSON，用来验证"闭环链路"；真实 `OpenAIClient` 的模型输出带 `tool_calls`、`finish_reason`、token 用量与成本。L1 已把 `usage`（token/成本）内置于 `LLMClient`，无论 Mock 还是真模型都能统计——这正对应 K1"成本与可观测是一等公民"，从第一天就埋点。
- **多步循环才是 Agent 本质**：新增的 `demo_multi_step` 演示"先算面积→再给答案"的两步闭环，印证 K1"Agent 不是一次函数调用"。真实任务循环往往更长（检索→推理→再检索），`max_steps` 双保险更关键。
- **真实接入时注意**：真模型 JSON 决策不稳定，需 K2 结构化输出约束 + K3 Function Calling 兜底，而非依赖 Mock 完美格式。

## 4. 若重做会改什么？
- 把"决策协议"从手写 JSON 升级为 K3 真正的 Function Calling（让模型返回 `tool_calls`）。
- 给 `Trajectory` 增加每步耗时字段，为 K12 评估铺垫。
- 接入真实 `OpenAIClient`（接口已预留），用 system 提示约束模型输出 JSON 决策。
