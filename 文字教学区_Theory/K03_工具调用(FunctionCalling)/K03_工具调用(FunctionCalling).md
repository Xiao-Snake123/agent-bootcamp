# K03 工具调用 Function Calling（对应执行阶段 P2）

> 本章把 L1 的"手写 JSON 决策"升级为工业级协议：让模型返回结构化的 `tool_calls`（工具名 + 合规参数），由代码安全执行。学完进入 `项目教学区_Labs/L03_工具调用实战/` 动手实现。

## 一、学习目标
学完你能：
1. 说清 Function Calling 是什么、与"让模型自由输出 JSON"的区别；
2. 描述工具描述（name / description / parameters JSON-Schema）三要素；
3. 区分串行调用与并行调用，知道何时用哪种；
4. 用 L3 把 `agent_core` 的工具注册表接入 Function Calling 协议并跑通。

## 二、核心概念
- **Function Calling**：模型不再吐自由文本，而是按你给的"工具清单"返回结构化调用请求 `tool_calls: [{name, arguments}]`，参数符合 JSON-Schema。执行与结果仍由你的代码负责（安全边界不变，呼应 K1 陷阱④）。
- **工具描述三要素**：`name`（唯一标识）、`description`（模型靠它选工具）、`parameters`（JSON-Schema，约束参数名 / 类型 / 必填）。
- **串行 vs 并行**：一次回复里可包含多个 `tool_calls`（并行，适合互相独立的子任务）；需前一步结果才能决定下一步的则串行（多轮）。
- **参数校验**：模型偶尔给出不合规参数，必须在 dispatch 前按 schema 校验 / 清洗（`agent_core` 的 `ToolRegistry.dispatch` 已做）。

## 三、工作原理
1. 你把一个或多个工具的"描述"随请求发给模型（OpenAI 格式：`tools=[{type:function, function:{name,description,parameters}}]`）。
2. 模型决定调用哪些工具，返回 `tool_calls`（含 `arguments` JSON）。
3. 你的代码逐个 dispatch，得到 `Observation`。
4. 把 `role=tool`（带 `name` / `tool_call_id`）消息回灌，模型据此产出下一步或最终答案。

这正是 L1 循环的"升级版"：L1 用手写 JSON，K3 用模型原生 `tool_calls` + schema 约束，解析失败率更低、工具可被发现。

## 四、主流方案
- **OpenAI / 兼容端点的 native function calling**：模型原生返回 `tool_calls`（本教学目标形态）。
- **JSON mode + 自写 schema**：退而求其次（L1/L2 的做法）。
- **框架封装**：LangChain Tool / MCP（K9）把工具描述自动转 schema。

## 五、常见陷阱
1. **description 太含糊**：模型选错工具；description 要写清"何时用、输入输出是什么"。
2. **schema 不严**：缺 `required` / 类型错，模型填出不合规参数，解析崩。
3. **并行调用强顺序依赖**：把有依赖的步骤并行，结果错乱；有依赖必须串行。
4. **不校验参数就执行**：模型可能给非法值；dispatch 前必须按 schema 清洗（呼应 K1 陷阱④）。
5. **tool 结果不加 name / tool_call_id**：多工具并行时模型无法对应，上下文错乱。

## 六、自检题
1. Function Calling 与"让模型输出 JSON"本质区别？
2. 工具描述三要素各起什么作用？
3. 什么场景必须串行而非并行？
4. 为什么 dispatch 前仍要校验参数？

## 七、动手引子
→ 进入 `项目教学区_Labs/L03_工具调用实战/`，运行 `python main.py` 看单工具与并行多工具的调用轨迹；`pytest test_fc.py` 验收 schema 转换、分发、参数校验与未知工具拒绝。
