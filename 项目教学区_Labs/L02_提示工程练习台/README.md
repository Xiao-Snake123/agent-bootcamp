# L02 提示工程练习台（对应 K2）

## 目标
一句话：动手组装"系统提示 + Few-shot + 结构化输出"的提示，并**亲手把一条糟糕提示改好**、看模型行为变化。
能力目标：理解 LLM 的上下文窗口约束，掌握可复用的 `PromptBuilder`，并真正会写（而不只是会组装）一条提示。

## 前置
- 已完成：`文字教学区_Theory/K02_提示与上下文(Prompt)/`（K2 理论章，重点读第四节"怎么写一条好提示"）
- 依赖：Python 3.11+；**无需 API Key**（用 Lab 内 `DemoLLM` / `ChallengeLLM` 离线演示"看系统提示行为"）

## 实现步骤
1. 读 `prompt.py` 的 `PromptBuilder`：`system / few-shot / query / structured_output` 如何拼成 messages（仅**组装**，内容按 K2 方法写）。
2. 读 `prompt.py` 的 `truncate_to_tokens` 与 `parse_json_block`：上下文截断与 JSON 抽取。
3. 读 `main.py` 的 `DemoLLM`：它真的读取 system 提示决定输出形态。
4. 读 `challenge.py`：BAD_SYSTEM / REFERENCE_GOOD / YOUR_SYSTEM 三段对照，及 `ChallengeLLM` 如何按格式约束切换行为。
5. 运行 `python main.py` 看 ①–④ 四类提示差异 + ⑤ 技能演练。

## 技能演练（本章重点）
打开 `challenge.py`，把 `YOUR_SYSTEM` 按 K2 第四节模板（角色/任务/约束/格式/示例）写成好提示，例如：
```
你是订餐意图解析助手。
任务：把用户口语转成 JSON。字段 intent（枚举 order/cancel/query）、items（数组，每项 name + qty）。
约束：只输出 JSON，不要解释。
示例：
用户：来两个汉堡
{"intent":"order","items":[{"name":"汉堡","qty":2}]}
```
保存后运行 `python main.py`，看 `[你的提示]` 是否吐出合规 JSON（对比 `[BAD 提示]` 的自由发挥）。

## 验收标准
- [ ] 能说出上下文窗口为什么是硬上限（含 lost-in-the-middle）
- [ ] `PromptBuilder` 生成的 messages 顺序正确（system → shots → query）
- [ ] 能按 K2 模板写出一条结构化提示，并让其产出 JSON
- [ ] `pytest test_prompt.py` 全绿

## 运行
```bash
cd 项目教学区_Labs/L02_提示工程练习台
python main.py
pytest test_prompt.py
```

## Reflection（回扣理论）
见 `reflection.md`。
