# Agent Bootcamp 网站重构整体规划（v2）

> 状态：方向已确认，阶段 1 进行中。推翻旧「K1–K12 浅中理论 + L1–L12 玩具 Lab」结构。
> 生成日期：2026-10-27

## 1. 新定位（推翻旧设想）
- **受众**：有 LLM / Python 基础的工程师（非入门）。
- **目标**：揭秘 Agent **全流程的工程化实现**——原理 → 形式化/伪代码 → 可运行代码 → 工业实践差异 → 论文依据 → 面试考点。
- **终局**：网站自身即**知识库语料源**，驱动一个**站内 RAG 求职复习 Agent 问答助手**。

## 2. 信息架构（页面图）

```
首页：Agent 工程化全景图（端到端流水线）+ 求职问答助手入口
├─ 认知篇：Agent 到底是什么（区别于 LLM App / Workflow）
│   ├─ LLM 能力边界、成本-延迟-能力三角、何时该/不该用 Agent
│   └─ 范式对比：ReAct / Plan-Execute / Reflexion / Multi-Agent（决策树）
├─ 核心机制篇（最重，12 章，逐层源码剖析）
│   1 推理-行动循环 ReAct   2 工具系统   3 上下文工程
│   4 规划与分解           5 反思与自修正 6 多 Agent
│   7 RAG 深度             8 能力扩展(MCP/FC/Skill) 9 编排与框架
│   10 评测与可观测        11 安全与合规  12 生产化 SRE
├─ 实战篇：端到端构建一个 Agent（贯穿项目，重生 agent_core）
├─ 求职篇：知识点图谱 / 高频面试题 / 系统设计题 / 简历包装
├─ 问答助手：基于本站语料的 RAG 求职复习（站内集成）
└─ 资源：论文 / 官方文档 / 开源 / 博客 / 书单 索引
```

## 3. 内容深度标准（每条固定包含）
原理 → 形式化/伪代码 → 可运行 Python 片段 → 工业实现差异（OpenAI/Anthropic/开源）→ 论文出处 → 面试考点 → 常见坑。

## 4. 知识库与站内问答助手架构
- **语料**：本站深度文档（带 metadata：主题/难度/是否面试题/来源）+ 外部采集文档。
- **管线**：抓取/清洗 → chunk(512~1024, overlap 128) → embedding(`DeepSeek`/`Voyage`/`Cohere`) → `Qdrant` → 检索 + rerank → `DeepSeek` 生成（带引用溯源）。
- **站内集成**：前端问答组件 → `FastAPI /ask` → 检索 + 生成；这正是 `.env` 中 DeepSeek / 向量库 key 的用武之地。

## 5. 技术栈（已确认）
- 前端：`Astro` + `React` 岛屿 + `Tailwind`；内容用 `MDX`。
- 后端（问答助手）：`FastAPI` 包 `agent_core` + `Qdrant` + `DeepSeek`。
- 部署：GitHub Pages（静态站）+ 后端 Vercel/Railway；或全 Vercel。

## 6. 现有代码工程处置
- **保留复用**：`agent_core`（LLM 抽象 + `build_llm` DeepSeek 接入）、`00_真实API接入`、`tutorial` 真实 Skill/MCP demo、评测思想。
- **重构**：K1–K12 旧理论**重写为深度版**；L1–L12 玩具 Lab **改为核心机制篇配套精简真实实现**（不再独立成「12 实验」）。
- **新增**：前端深度内容站、知识库构建 pipeline、站内问答助手；Capstone 升级为「构建一个求职复习 Agent 助手」本身。

## 7. 推进阶段
1. 规划 + 资料清单 + 内容大纲（本次）。
2. 写核心机制篇 12 章深度文档。
3. 重生 `agent_core` + 每章可运行 demo（接 DeepSeek）。
4. 前端站 + 站内 RAG 问答助手。
5. 求职篇（知识点图谱 + 面试题库）。

## 8. 资料来源（详见 references/sources.md）
优先级：官方文档 + Lilian Weng 综述 + 5~6 篇核心论文 + LangGraph/LlamaIndex 文档，覆盖 80% 深度内容。
