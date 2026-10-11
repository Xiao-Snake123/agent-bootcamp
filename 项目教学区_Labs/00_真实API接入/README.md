# 真实 API 接入（配置 key）

> 把 Agent Bootcamp 从离线 Mock 切到真实 LLM。所有 key 集中在项目根 `.env`（已被 `.gitignore` 忽略，绝不入库）。`.env.example` 是模板，可提交、无密钥。

## 1. 配置步骤
```bash
cd Agent Bootcamp
cp .env.example .env          # 仅首次；之后直接编辑 .env
# 用编辑器打开 .env，把真实 key 填到等号右边，例如 OPENAI_API_KEY=sk-xxxx
pip install -r requirements.txt   # 装 openai / anthropic / python-dotenv 等
```

## 2. 支持的 provider（在 .env 填对应 key 即可）
| provider | 需要的 key | 说明 |
|----------|-----------|------|
| `openai` | `OPENAI_API_KEY` | 默认后端（gpt-4o-mini 等） |
| `deepseek` | `DEEPSEEK_API_KEY` | 兼容 OpenAI 协议，base_url 已预设 |
| `dashscope` | `DASHSCOPE_API_KEY` | 通义千问（阿里云） |
| `zhipu` | `ZHIPU_API_KEY` | 智谱 GLM（清华） |
| `custom` | `CUSTOM_BASE_URL`+`CUSTOM_API_KEY`+`CUSTOM_MODEL` | 任意 OpenAI 兼容网关 |
| `anthropic` | `ANTHROPIC_API_KEY` | Claude 独立 SDK |

## 3. 在代码里接入
```python
from agent_core import build_llm, Agent

llm = build_llm("openai")          # 自动读 .env 的 OPENAI_API_KEY
# 之后把 llm 传给任意 Lab 的 Agent(llm=...) 即可走真实模型
```

## 4. 连通性验证
```bash
cd 项目教学区_Labs
python 00_真实API接入/quickstart.py     # 改 PROVIDER 为你用的；填好 key 后运行
```

## 5. 接 Agent 时的重要提示（JSON 协议）
`agent_core.Agent` 用简化 JSON 协议（`{"action":..,"args":..}` 或 `{"final_answer":..}`）。真实模型需被**系统提示要求输出该格式**才会走通工具循环。建议 system 提示加：
> 你只能用 JSON 回复：要调用工具时输出 {"thought":..,"action":"<工具名>","args":{..}}；能直接回答时输出 {"thought":..,"final_answer":".."}。

（K3 工具调用实战另有真 Function Calling 写法，优先按该 Lab 示例。）

## 6. 各模块需要哪些 key（对照表）
| 模块 | 需要的 key |
|------|-----------|
| 基础 LLM（K1–K7, K11） | `OPENAI_API_KEY` 或任一 provider key |
| K8 RAG | `VOYAGE_API_KEY`/`COHERE_API_KEY`（嵌入）+ `PINECONE_API_KEY`/`QDRANT_API_KEY`/`WEAVIATE_API_KEY`（云端向量库；本地 Chroma 不需要） |
| K9 MCP | 按所用 server：`GITHUB_PERSONAL_ACCESS_TOKEN`/`SLACK_BOT_TOKEN`/`NOTION_API_KEY`（文件系统类不需要） |
| Capstone 主题A（研究助理） | 上述 LLM + `TAVILY_API_KEY`/`SERPER_API_KEY`/`BRAVE_SEARCH_API_KEY`（联网搜索） |
| K12 可观测 | `LANGSMITH_API_KEY` + `LANGCHAIN_TRACING_V2=true` |

> 安全：`.env` 含密钥，已 gitignore；切勿把真实 key 粘贴到聊天或提交。
