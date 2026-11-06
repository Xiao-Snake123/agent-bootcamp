# 第 1 章 推理-行动循环 ReAct

> 难度：★★☆☆☆ ｜ 前置：会用 LLM API、了解 prompt 基本概念 ｜ 对应旧 K1/K2

## 1.1 为什么需要 ReAct
纯 LLM 只能"想"（生成文本），不能直接"做"（查数据库、调 API、算数）。早期做法是把任务写死成 Chain（固定步骤）。ReAct（Reasoning + Acting）把**推理**和**行动**交织进同一个循环：模型先输出一段 Thought（为什么这么做），再输出 Action（调哪个工具、参数），环境返回 Observation，模型据此继续思考，直到能给出最终答案。

关键点：**推理轨迹本身被写回上下文，成为下一步决策的输入**——这让 Agent 能基于"刚才看到了什么"动态调整，而不是盲走固定流程。

## 1.2 核心结构：Thought / Action / Observation
- **Thought**：自然语言推理，解释当前状态与下一步意图（给人看、也给模型自己看）。
- **Action**：结构化指令，含 `tool` 名与 `args`（通常 JSON）。
- **Observation**：工具执行结果，被原样回注上下文。
- **循环终止**：当模型不再产出 Action，而是产出 `final_answer` 时停止。

## 1.3 形式化
```
state = [system_prompt, user_goal]
while not done:
    decision = LLM(state)                  # 返回 {thought, action|final_answer}
    if decision has final_answer:
        return decision.final_answer
    obs = execute(decision.action)          # 调用工具，捕获结果/异常
    state.append(Thought(decision.thought))
    state.append(Action(decision.action))
    state.append(Observation(obs))
```
注意：`execute` 必须把异常也转成 Observation（如 `"error: ..."`），否则一次工具失败就会打断循环。

## 1.4 可运行最小实现（Python，独立可跑）
下面是一段**不依赖任何框架**的最小 ReAct，便于看清机制（接 OpenAI 兼容接口）：

```python
import json, os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOOLS = {
    "calculator": lambda expr: str(eval(expr, {"__builtins__": {}}, {})),
}

SYSTEM = (
    "你是 ReAct Agent。每步输出 JSON："
    '{"thought":"...","action":"工具名","args":{"expr":"1+1"}} '
    '或 {"thought":"...","final_answer":"..."}。可用工具：calculator。'
)

def run(goal, max_steps=5):
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": goal}]
    for step in range(max_steps):
        resp = client.chat.completions.create(
            model="gpt-4o-mini", messages=msgs,
            response_format={"type": "json_object"},
        )
        dec = json.loads(resp.choices[0].message.content)
        if "final_answer" in dec:
            return dec["final_answer"]
        # 执行动作
        fn = TOOLS.get(dec["action"])
        try:
            obs = fn(**dec["args"]) if fn else "unknown tool"
        except Exception as e:
            obs = f"error: {e}"
        msgs.append({"role": "assistant", "content": json.dumps(dec, ensure_ascii=False)})
        msgs.append({"role": "user", "content": f"Observation: {obs}"})
    return "（步数耗尽，未得出答案）"

print(run("帮我算 (12+8)*3 是多少"))
```
要点：Observation 以 `user` 角色回注（很多实现用 `tool` 角色，等价）；`response_format=json_object` 强制结构化；异常被吞进 Observation 而非抛出。

## 1.5 工业实现差异
- **OpenAI**：用 `tools` 参数 + `tool_calls` 字段，模型返回的是函数调用对象而非手写 JSON，解析更稳；支持并行 `tool_calls`。
- **Anthropic**：`tool_use` 内容块，system 需单独传，不支持把工具结果伪装成普通 user 文本（要用 `tool_result` 角色）。
- **开源（LangGraph 等）**：把"思考/动作/观察"抽象成 Graph 节点，Observation 走状态通道，便于 checkpoint 与人工回环（见第 9 章）。

## 1.6 论文与延伸
- ReAct: Synergizing Reasoning and Acting in Language Models（Yao et al., 2022, arXiv:2210.03629）——原始论文，含 HotpotQA / FEVER 等基准。
- 延伸：Reflexion（第 5 章）在 ReAct 基础上加"反思"节点；Plan-and-Execute（第 4 章）先整体规划再循环执行。

## 1.7 面试考点
1. **ReAct 与纯 Chain / 直接 prompt 的区别？** 答：ReAct 引入环境反馈闭环，能根据 Observation 动态修正，而非一次性生成；适合需外部信息或不确定步骤的任务。
2. **如何防止 Agent 死循环 / 无限调用工具？** 答：设 `max_steps`；对重复 Action 做去重/惩罚；用反思模块（第 5 章）检测停滞。
3. **长轨迹下上下文溢出怎么办？** 答：摘要压缩（第 3 章）、只保留关键 Observation、把长期事实移入记忆。

## 1.8 常见坑
- **把 Observation 直接当成普通对话拼接**，导致格式错乱或模型把"Observation:"当成用户指令——应走规范的 tool/tool_result 通道。
- **不设步数上限且无成本护栏**，模型偶尔会反复调同一工具烧钱（呼应第 10/12 章的成本治理）。
- **工具失败就抛异常中断循环**，正确做法是转成 Observation 让模型自我纠错。
