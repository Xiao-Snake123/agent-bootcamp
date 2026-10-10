# L03 工具调用实战（对应 K3）

## 目标
一句话：把 `agent_core` 的工具注册表接入 Function Calling 协议，跑通单工具与并行多工具调用。
能力目标：理解 `tool_calls` 协议、工具 JSON-Schema 描述、参数校验与串行 / 并行。

## 前置
- 已完成：`文字教学区_Theory/K03_工具调用(FunctionCalling)/`（K3 理论章）
- 已铺垫：`L01_最小AgentLoop`（Agent 闭环）、`L02_提示工程练习台`（提示构造）
- 依赖：Python 3.11+；**无需 API Key**（用 `MockFunctionCaller` 离线决策器）

## 实现步骤
1. 读 `tools_fc.py`：工具如何用 name / description / parameters(JSON-Schema) 自描述。
2. 读 `fc.py` 的 `tools_to_openai_schema`：把注册表转成 OpenAI tools 参数。
3. 读 `fc.py` 的 `FunctionCallingAgent.run`：模型返回 tool_calls → 逐个 dispatch → 回灌。
4. 读 `mock_fc.py`：离线决策器如何按关键词产出合规 tool_calls（含并行）。
5. 运行 `python main.py` 看单工具 / 并行轨迹。

## 验收标准
- [ ] 能说出 Function Calling 与"手写 JSON"的区别
- [ ] `tools_to_openai_schema` 转换正确（type / function / name / parameters）
- [ ] `pytest test_fc.py` 全绿（含并行、参数校验、未知工具拒绝）

## 运行
```bash
cd 项目教学区_Labs/L03_工具调用实战
python main.py
pytest test_fc.py
```

## Reflection（回扣理论）
见 `reflection.md`。
