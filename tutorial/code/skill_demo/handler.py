"""doc-search Skill 的处理函数（纯 Python，可单独测试）。"""
CORPUS = {
    "mcp": "MCP 是让大模型统一接入工具与数据的开放协议。",
    "rag": "RAG 先检索再生成，降低幻觉。",
    "agent": "Agent 能自主调用工具、记忆与规划。",
}


def search(query: str) -> str:
    """对查询做关键词匹配，返回命中文档片段。"""
    q = query.lower()
    hits = [v for v in CORPUS.values() if q in v.lower()]
    return "\n".join(hits) if hits else f"未找到与「{query}」相关的内容。"
