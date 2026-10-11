---
name: doc-search
description: 当需要从内部知识库检索资料时使用。提供关键词检索能力，可被 Agent 在运行时按需加载。
triggers:
  - 检索
  - 知识库
  - 查资料
  - 找文档
---
# doc-search Skill

一个最小可复用的「能力模块」示例：名称 + 描述 + 触发词 + 处理函数。
Agent 在主循环里识别到触发词后，加载本 Skill 并调用 handler.search()。
