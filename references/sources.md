# 资料来源清单（Agent 工程化深度内容 + 求职语料）

> 用途：支撑 `00_规划与调研/content_outline.md` 中核心机制篇 12 章的深度内容，
> 并最终汇入站内 RAG 求职问答助手的知识库。
> 优先级：P0 必读、P1 重要、P2 拓展。采集时建议保留原文 + 出处 metadata。

## 1. 官方文档 / 最佳实践（P0）
| 名称 | 链接 | 对应章节 | 用途 |
|---|---|---|---|
| Anthropic《Building Effective Agents》 | https://www.anthropic.com/research/building-effective-agents | 认知篇/编排 | 工作流 vs Agent、常见模式 |
| OpenAI API 文档 | https://platform.openai.com/docs | 工具/FC | 工具调用协议细节 |
| OpenAI Cookbook | https://github.com/openai/openai-cookbook | 各章 | 可运行示例 |
| LangGraph 文档 | https://langchain-ai.github.io/langgraph/ | 编排(9) | 状态机/checkpoint 源码级 |
| LlamaIndex 文档 | https://docs.llamaindex.ai/ | RAG(7) | 检索/rerank 实践 |
| MCP 官方规范 | https://modelcontextprotocol.io | 能力扩展(8) | MCP 协议 |
| Microsoft AutoGen | https://microsoft.github.io/autogen/ | 多 Agent(6) | 多 Agent 框架 |
| CrewAI 文档 | https://docs.crewai.com/ | 多 Agent(6) | 角色编排 |

## 2. 核心论文（arXiv，P0/P1）
| 论文 | arXiv | 章节 | 关键词 |
|---|---|---|---|
| ReAct: Synergizing Reasoning and Acting | https://arxiv.org/abs/2210.03629 | 1,2 | 推理-行动循环 |
| Reflexion: Language Agents with Verbal RL | https://arxiv.org/abs/2303.11366 | 5 | 反思自修正 |
| Toolformer | https://arxiv.org/abs/2302.04761 | 2,8 | 工具调用学习 |
| Tree of Thoughts | https://arxiv.org/abs/2305.10601 | 4 | 规划分解 |
| Generative Agents (Stanford) | https://arxiv.org/abs/2304.03442 | 6 | 多 Agent 社会 |
| Self-RAG | https://arxiv.org/abs/2310.11511 | 7,10 | 自适应检索/评测 |
| AutoGen | https://arxiv.org/abs/2308.08155 | 6 | 多 Agent 框架 |
| AgentBench | https://arxiv.org/abs/2308.03688 | 10 | Agent 评测基准 |
| CRITIC / Self-Consistency | 见 arxiv 搜索 | 5,10 | 验证/采样策略 |

> 采集建议：保存 PDF + 用一句话摘要 + 标注「贡献点 / 局限 / 工业落地差距」。

## 3. 深度博客 / 综述（P0）
| 名称 | 链接 | 用途 |
|---|---|---|
| Lilian Weng《LLM Powered Autonomous Agents》 | https://lilianweng.github.io/posts/2023-06-23-agent/ | 总纲式综述，必读 |
| Chip Huyen《The Rise of Agentic AI》 | https://huyenchip.com/ （博客搜 agents） | 工程化视角 |
| Hugging Face Blog | https://huggingface.co/blog | 技术实现 |
| Eugene Yan / Simon Willison 博客 | https://eugeneyan.com/ 、https://simonwillison.net/ | 生产经验 |

## 4. 开源项目源码（P1，学实现而非概念）
- LangGraph、AutoGen、CrewAI、Haystack、DSPy、LiteLLM、PromptFoo（评测）。
- 重点读：编排状态机、工具路由、记忆接口、评测 harness 的实现。

## 5. 书 / 课（P1/P2）
- DeepLearning.AI《AI Agent》短课程：https://www.deeplearning.ai/short-courses/
- Chip Huyen《Designing Machine Learning Systems》（工程方法论迁移）
- 各类 LLM 应用构建书（挑 1~2 本即可，避免重复）。

## 6. 站内已有可复用资产
- `recruitment_analysis/Agent与AI应用开发_技术趋势报告.md`：求职市场背书。
- `tutorial/code/skill_demo`、`tutorial/code/mcp_demo`：实战篇素材。
- `agent_core`：`build_llm` 已接 DeepSeek，问答助手后端直接复用。

## 7. 采集与入库流程（待阶段 4 实现）
1. 按上表下载/抓取 → 存 `references/corpus/raw/`。
2. 清洗（去导航/广告）→ `references/corpus/clean/`。
3. chunk + 打 metadata → 向量化进 Qdrant。
4. 定期追加本站新写的深度文档（同源语料）。
