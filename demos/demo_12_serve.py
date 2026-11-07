"""第 12 章 · 生产化 SRE：把 agent_core 包成 FastAPI 服务。

用 TestClient 在进程内验证 /health、/chat、/run_agent 三个端点
（offline=True，零成本，不需要起 uvicorn）。
实际部署：uvicorn agent_core.serve:app --port 8001
文档：content/核心机制篇/12_生产化SRE.md
"""
from _shared import run


def body(llm, args):
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        print("跳过：缺少 httpx，请先 pip install httpx")
        return
    from agent_core.serve import create_app

    app = create_app(offline=True)
    client = TestClient(app)

    health = client.get("/health").json()
    print("GET /health ->", health)

    chat = client.post("/chat", json={"goal": "请算 6*7 等于多少", "max_steps": 4}).json()
    print("POST /chat ->", chat)

    detail = client.post("/run_agent",
                         json={"goal": "请算 6*7 等于多少", "max_steps": 4}).json()
    if "stop_reason" not in detail:
        print("POST /run_agent 异常响应:", detail)
        return
    print("POST /run_agent -> stop_reason =", detail["stop_reason"],
          "| steps =", len(detail["steps"]), "| usage =", detail["usage"])
    print("要点：生产还要补流式、限流/熔断、语义缓存、超时、降级与 p99 监控；"
          "本 demo 只验证服务封装与可观测字段。")


if __name__ == "__main__":
    run(12, "生产化 SRE（FastAPI 封装）", body)
