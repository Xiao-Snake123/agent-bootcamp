# K02 LLM 基础与提示工程（对应执行阶段 P1）

> 本章讲清 Agent 的"大脑"——LLM——到底是什么、受什么约束，以及我们如何用"提示"指挥它。学完进入 `项目教学区_Labs/L02_提示工程练习台/` 动手拼装提示词。

## 一、学习目标
学完你能：
1. 说清 token 是什么、上下文窗口为何是硬上限；
2. 区分系统提示 / 用户提示 / Few-shot，讲清各自作用；
3. 理解"结构化输出"为什么对 Agent 至关重要；
4. 用 L2 的 `PromptBuilder` 拼出带系统提示 + Few-shot + 结构化约束的 messages。

## 二、核心概念
- **Token**：模型的最小处理单位（英文约 1 词≈1 token，中文约 1–2 字≈1 token）。所有长度、价格、延迟都按 token 计。
- **上下文窗口（Context Window）**：模型单次能"看到"的最大 token 数（如 8k / 32k / 128k）。超出部分只能截断，或靠 K4 记忆 / 摘要压缩 / K8 检索来腾空间。它是 Agent 的"短期记忆容量上限"。
- **系统提示（System Prompt）**：设定角色、规则、输出格式，优先级最高，通常在一轮对话开头注入一次。
- **用户提示（User Prompt）**：本次真实输入 / 目标（来自 K1 的 `goal`）。
- **Few-shot（少样本）**：在 system 之后、query 之前塞几个 `(输入, 期望输出)` 示范，让模型"照葫芦画瓢"，比纯文字描述更稳。
- **结构化输出（Structured Output）**：要求模型只吐 JSON / 固定 schema。Agent 的代码要靠它解析决策（K3 升级为 Function Calling）。

## 三、工作原理
发给模型的 messages 本质是一个有序列表：

```
[system] → [user/assistant 交替的 few-shot] → [user 真实 query]
```

模型按这个序列自回归生成下一段。Agent 的关键技巧：
- 用 system 锁死"你只能输出决策 JSON"；
- 用 few-shot 给格式样板；
- 用结构化约束降低解析失败率。

L2 的 `PromptBuilder` 就是把这套组装过程变成可复用代码——它产出 `List[dict]`，可以直接喂给 `agent_core` 的 `LLMClient.complete(messages)`。

## 四、主流方案
- **提示模板引擎**：Jinja / 自写 `PromptBuilder`（本教学用后者，零依赖）。
- **结构化输出**：JSON mode、Function Calling、或 Pydantic 约束（K3 深入）。
- **长上下文处理**：截断 / 滑动窗口 / 摘要压缩 / 向量检索（K4、K8）。

## 五、常见陷阱
1. **忽视上下文窗口**：把整库文档塞进 prompt 直接超限，模型"失忆"。
2. **系统提示被用户覆盖**：用户提示若含"忽略以上指令"，可能越权；需在 K11 做防护。
3. **Few-shot 与真实分布不符**：示例格式和线上不一致，模型学歪。
4. **不要求结构化输出**：让模型自由发挥，代码解析失败、循环崩（这正是 L1 必须坚持 JSON 决策的原因）。
5. **在 prompt 里算数 / 查实时数据**：模型不擅长，应交工具（K3）。

## 六、自检题
1. 中文"你好世界"大约多少 token？为什么只能估算？
2. 系统提示、Few-shot、用户提示的先后顺序与作用？
3. 为什么 Agent 几乎都要"结构化输出"？
4. 上下文窗口满了，不截断还能怎么办（列举两种）？

## 七、动手引子
→ 进入 `项目教学区_Labs/L02_提示工程练习台/`，运行 `python main.py` 看同一句话在"有无系统提示 / 有无 few-shot / 是否要求 JSON"下输出如何变化；再 `pytest test_prompt.py` 验收 `PromptBuilder`。
