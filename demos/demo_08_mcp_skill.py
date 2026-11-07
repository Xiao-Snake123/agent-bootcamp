"""第 8 章 · 能力扩展：真实 MCP 子进程 + Skill frontmatter + DeepSeek 决策。

复用 tutorial/code/mcp_demo/server.py（stdio JSON-RPC 2.0 三段协议），
把远端 tools/list 动态映射为 agent_core 的 Tool，并让 LLM 决定何时调用——
这正是「MCP 是工具接入协议、FC 是调用原语、Skill 是可复用能力包」的分层。
文档：content/核心机制篇/08_能力扩展(MCP-FC-Skill).md
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from _shared import (Agent, Observation, TUTORIAL_DIR, ToolRegistry,
                     make_tool, run, show_trajectory, tool_call)


class MCPClient:
    """最小 MCP stdio 客户端：initialize → notifications/initialized → tools/*。"""

    def __init__(self, server_py: Path):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}  # 两端统一 UTF-8，避免中文乱码
        self.proc = subprocess.Popen(
            [sys.executable, str(server_py)], cwd=str(server_py.parent),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
            encoding="utf-8", env=env)
        self._id = 0

    def _request(self, method, params=None):
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method,
                   "params": params or {}}
        self.proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        return json.loads(line) if line.strip() else {"error": {"message": "无响应"}}

    def _notify(self, method):
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.proc.stdin.flush()

    def initialize(self):
        resp = self._request("initialize", {"protocolVersion": "2024-11-05"})
        self._notify("notifications/initialized")
        return resp

    def list_tools(self):
        return self._request("tools/list").get("result", {}).get("tools", [])

    def call_tool(self, name, arguments) -> Observation:
        resp = self._request("tools/call", {"name": name, "arguments": arguments})
        if "error" in resp:                       # 协议级错误传播
            return Observation(f"MCP 错误：{resp['error']}", ok=False)
        result = resp.get("result", {})
        text = "\n".join(c.get("text", "") for c in result.get("content", []))
        return Observation(text, ok=not result.get("isError", False))

    def close(self):
        try:
            self.proc.terminate()
        except Exception:
            pass


def body(llm, args):
    server = TUTORIAL_DIR / "mcp_demo" / "server.py"
    if not server.exists():
        print(f"跳过：未找到 {server}")
        return
    mcp = MCPClient(server)
    try:
        init = mcp.initialize()
        print("initialize ->", init.get("result", {}).get("protocolVersion"))
        remote = mcp.list_tools()
        print("tools/list ->", [t["name"] for t in remote])

        registry = ToolRegistry()
        for spec in remote:
            registry.register(make_tool(
                spec["name"], spec.get("description", ""),
                spec.get("inputSchema", {"type": "object", "properties": {}}),
                lambda _name=spec["name"], **kw: mcp.call_tool(_name, kw)))
        print("映射后的 OpenAI tools schema:", registry.openai_schemas()[0]["function"]["name"])

        # 错误传播：未知工具 / 工具自身 isError 都不能让主流程崩
        print("错误传播（未知工具）:", registry.dispatch("no_such_tool", {}).content[:80])

        # Skill：元数据驱动的能力包（frontmatter）
        skill_file = TUTORIAL_DIR / "skill_demo" / "SKILL.md"
        if skill_file.exists():
            text = skill_file.read_text(encoding="utf-8")
            fm = re.search(r"^---\s*(.*?)\s*---", text, re.S)
            print("Skill frontmatter:", " ".join(fm.group(1).split())[:120] if fm else "（无）")

        agent = Agent(llm, registry,
                      system="需要查资料时调用 doc_search 工具，然后基于返回内容用一句话总结。")
        answer, traj = agent.run(
            args.goal or "请用 doc_search 查一下 MCP 是什么，并总结", max_steps=4)
        print("\n最终答案:", answer)
        show_trajectory(traj)
        print("要点：MCP server 应沙箱隔离、设超时与熔断；错误转成观察而非异常中断主 Agent。")
    finally:
        mcp.close()


if __name__ == "__main__":
    run(8, "能力扩展（真实 MCP + Skill + FC）", body,
        script=[tool_call("doc_search", query="MCP")])
