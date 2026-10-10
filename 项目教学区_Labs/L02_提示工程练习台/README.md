# L02 提示工程练习台（对应 K2）

## 目标
一句话：动手拼装"系统提示 + Few-shot + 结构化输出"的提示，并看到它如何改变模型行为。
能力目标：理解 LLM 的上下文窗口约束，掌握可复用的 `PromptBuilder`。

## 前置
- 已完成：`文字教学区_Theory/K02_提示与上下文(Prompt)/`（K2 理论章）
- 依赖：Python 3.11+；**无需 API Key**（用 Lab 内 `DemoLLM` 离线演示"看系统提示行为"）

## 实现步骤
1. 读 `prompt.py` 的 `PromptBuilder`：`system / few-shot / query / structured_output` 如何拼成 messages。
2. 读 `prompt.py` 的 `truncate_to_tokens` 与 `parse_json_block`：上下文截断与 JSON 抽取。
3. 读 `main.py` 的 `DemoLLM`：它真的读取 system 提示决定输出形态，离线演示提示工程效果。
4. 运行 `python main.py` 对比四种提示下的输出。

## 验收标准
- [ ] 能说出上下文窗口为什么是硬上限
- [ ] `PromptBuilder` 生成的 messages 顺序正确（system → shots → query）
- [ ] `pytest test_prompt.py` 全绿

## 运行
```bash
cd 项目教学区_Labs/L02_提示工程练习台
python main.py
pytest test_prompt.py
```

## Reflection（回扣理论）
见 `reflection.md`。
