"""第 6 章 · 多 Agent 协作：结构化消息 + 共享黑板 + 死锁检测。

看什么：角色轮流发言、消息带 sender/recipient、Orchestrator 统一裁决 done；
整轮消息重复时判定互相推诿并终止（防无限委派）。
文档：content/核心机制篇/06_多智能体.md
"""
from _shared import Blackboard, MockLLMClient, MultiAgent, run

ROLES = {"研究员": "查证事实、归纳要点，把发现交给工程师",
         "工程师": "基于研究员的要点产出可落地方案，并对 user 交付"}


def body(llm, args):
    goal = args.goal or "为一个 Agent 服务设计最小可观测方案"
    team = MultiAgent(llm, ROLES, max_rounds=4)
    final, board, reason = team.run(goal)
    print("终止原因:", reason)
    print("最终交付:", final)
    print("\n黑板消息:")
    for m in board.read():
        print(f"  [{m.kind}] {m.sender} -> {m.recipient}: {m.content[:100]}")

    # 离线时额外演示死锁检测：两轮完全相同的推诿消息
    if llm.model == "mock":
        stall = MockLLMClient(script=[
            '{"to":"工程师","content":"你先做","done":false}',
            '{"to":"研究员","content":"你先做","done":false}',
        ] * 4)
        dead = MultiAgent(stall, ROLES, max_rounds=4)
        f2, b2, r2 = dead.run(goal)
        print(f"\n死锁演示: 终止原因={r2} | 消息数={len(b2.messages)} | 交付={f2!r}")
        print("要点：终止条件必须写在编排层（max_rounds / 重复检测），不能靠模型自觉。")


if __name__ == "__main__":
    script = [
        '{"to":"工程师","content":"要点：记录每步 tool_calls、耗时、token 与失败原因",'
        '"done":false}',
        '{"to":"user","content":"最小可观测方案：轨迹落盘 + 关键指标埋点 + 失败回放",'
        '"done":true}',
    ]
    run(6, "多 Agent 协作（消息总线 / 死锁检测）", body, script=script)
