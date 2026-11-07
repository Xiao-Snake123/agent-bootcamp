"""FastAPI 封装（第 12 章 / content_outline.md「serve.py」锚点）。

把 agent_core 以 HTTP 暴露，供站内问答助手（backend/rag_server.py）复用：
    uvicorn agent_core.serve:app --port 8001
"""
from __future__ import annotations

try:
    from pydantic import BaseModel

    class GoalIn(BaseModel):
        """请求体必须定义在模块级：局部类会让 FastAPI 误判成 query 参数（422）。"""
        goal: str
        max_steps: int = 8

except ImportError:      # 未装 fastapi/pydantic 时本模块仍可被导入
    GoalIn = None


def create_app(provider: str = "deepseek", offline: bool = False,
               max_cost: float | None = None, system: str = ""):
    from fastapi import FastAPI

    from .agent import Agent
    from .config import auto_llm, build_llm
    from .tools import ToolRegistry, make_tool

    llm = build_llm(provider, offline=offline, max_cost=max_cost) if offline \
        else auto_llm(provider, max_cost=max_cost)
    registry = ToolRegistry()
    registry.register(make_tool(
        "calculator", "计算四则运算表达式",
        {"type": "object", "properties": {"expr": {"type": "string"}},
         "required": ["expr"]},
        lambda expr: _safe_calc(expr)))
    agent = Agent(llm, registry, system=system or "需要计算时调用 calculator 工具。")

    app = FastAPI(title="agent_core serve（Agent 工程化统一接口）")

    @app.get("/health")
    def health():
        return {"status": "ok", "provider": provider, "model": llm.model,
                "offline": llm.model == "mock",
                "tools": [t.name for t in registry.list()]}

    @app.post("/chat")
    def chat(body: GoalIn):
        answer, traj = agent.run(body.goal, max_steps=body.max_steps)
        return {"answer": answer, "stop_reason": traj.stop_reason}

    @app.post("/run_agent")
    def run_agent(body: GoalIn):
        answer, traj = agent.run(body.goal, max_steps=body.max_steps)
        return {"answer": answer, "stop_reason": traj.stop_reason,
                "steps": [{"action": s.action, "observation": s.observation, "ok": s.ok}
                          for s in traj.steps],
                "usage": {"calls": llm.usage.calls, "cost": round(llm.usage.cost, 6),
                          "total_tokens": llm.usage.total_tokens}}
    return app


def _safe_calc(expr: str) -> str:
    """受限四则运算求值（不 eval 任意代码）。"""
    import ast
    import operator
    ops = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv,
           ast.Pow: operator.pow}

    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return +ev(node.operand) if isinstance(node.op, ast.UAdd) else -ev(node.operand)
        raise ValueError("仅支持四则运算")

    return str(ev(ast.parse(expr, mode="eval").body))


app = create_app()
