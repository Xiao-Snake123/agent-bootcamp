#!/usr/bin/env python3
"""验证 MCP 服务：initialize -> tools/list -> tools/call 全链路跑通。"""
import subprocess
import json
import sys

proc = subprocess.Popen(
    [sys.executable, "server.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
)


def send(obj):
    proc.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
    proc.stdin.flush()


def recv():
    line = proc.stdout.readline()
    return json.loads(line) if line.strip() else None


send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
print("initialize ->", recv())

send({"jsonrpc": "2.0", "method": "notifications/initialized"})  # 通知，无回复

send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
print("tools/list ->", recv())

send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
      "params": {"name": "doc_search", "arguments": {"query": "MCP"}}})
print("tools/call ->", recv())

proc.terminate()
