#!/usr/bin/env python3
"""最小可用的 MCP 服务（stdio 传输，纯标准库实现）。

演示 Model Context Protocol 的核心：通过 JSON-RPC 2.0 在 stdin/stdout 上
暴露「工具(tools)」。无需任何第三方依赖，可被支持 MCP 的客户端直接接入。

运行：python server.py   （由 MCP 客户端以子进程方式拉起，读写 stdin/stdout）
"""
import sys
import json
import traceback

PROTOCOL_VERSION = "2024-11-05"

# 一个极简内存知识库，模拟 RAG 的检索语料
CORPUS = {
    "mcp": "MCP（Model Context Protocol）是 Anthropic 提出的开放协议，让大模型以统一方式接入外部工具与数据源。",
    "rag": "RAG（检索增强生成）先检索相关文档片段，再连同问题一起送给大模型，降低幻觉、引入私有知识。",
    "agent": "Agent 是能自主调用工具、记忆上下文、循环规划来完成目标的程序。",
}


def list_tools():
    """tools/list：告诉客户端本服务能提供哪些工具。"""
    return {
        "tools": [
            {
                "name": "doc_search",
                "description": "在内部知识库中检索与关键词相关的片段，演示 RAG 式检索。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "检索关键词"}
                    },
                    "required": ["query"],
                },
            }
        ]
    }


def call_tool(name, arguments):
    """tools/call：真正执行工具，返回 {content:[...]}。"""
    if name == "doc_search":
        q = (arguments or {}).get("query", "")
        hits = [v for v in CORPUS.values() if q.lower() in v.lower()]
        text = "\n".join(hits) if hits else f"未找到与「{q}」相关的内容。"
        return {"content": [{"type": "text", "text": text}], "isError": False}
    return {"content": [{"type": "text", "text": f"未知工具: {name}"}], "isError": True}


def handle(message):
    method = message.get("method")
    msg_id = message.get("id")
    if msg_id is None:          # 通知（无 id）不回复
        return None
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "doc-search-mcp", "version": "0.1.0"},
        }}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": list_tools()}
    if method == "tools/call":
        params = message.get("params", {})
        return {"jsonrpc": "2.0", "id": msg_id, "result": call_tool(params.get("name"), params.get("arguments"))}
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"方法不存在: {method}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            resp = handle(msg)
        except Exception:
            resp = {"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32603, "message": traceback.format_exc()}}
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
