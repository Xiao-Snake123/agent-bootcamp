"""多 Agent 协作（第 6 章）：结构化消息 + 共享黑板 + 死锁检测。

对应 content_outline.md 第 6 章锚点「agent_core/multi.py（新增）」。
角色轮流发言（消息总线），Orchestrator 由 run() 统一裁决终止，避免无限互相委派。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ._util import extract_json


@dataclass
class Message:
    sender: str
    recipient: str
    content: str
    kind: str = "task"        # task / answer / done


class Blackboard:
    """共享黑板：所有消息可追溯，用于去重与循环检测。"""

    def __init__(self):
        self.messages: list = []
        self.round = 0

    def post(self, message: Message) -> Message:
        self.messages.append(message)
        return message

    def read(self, limit: int = 12) -> list:
        return self.messages[-limit:]

    def transcript(self, limit: int = 12) -> str:
        return "\n".join(f"{m.sender} -> {m.recipient}: {m.content[:160]}"
                         for m in self.read(limit))


class MultiAgent:
    """LLM 驱动的角色团队。每轮每个角色发一条结构化消息。"""

    def __init__(self, llm, roles: dict, max_rounds: int = 5):
        self.llm = llm
        self.roles = roles          # {"研究员": "负责查证与归纳", ...}
        self.max_rounds = max_rounds

    def _speak(self, role: str, duty: str, goal: str, board: Blackboard) -> Message:
        prompt = (f"你是团队中的「{role}」，职责：{duty}。\n团队目标：{goal}\n"
                  f"当前黑板：\n{board.transcript()}\n"
                  '只输出 JSON：{"to":"接收角色名或 user","content":"你的产出",'
                  '"done":false}。若你判定目标已完成，把 to 设为 "user"、done 设为 true，'
                  "并在 content 里给出最终交付。")
        raw = self.llm.complete([
            {"role": "system", "content": "你是多 Agent 团队成员，只输出 JSON。"},
            {"role": "user", "content": prompt}])
        data = extract_json(raw)
        if not isinstance(data, dict):
            # 离线兜底：第一个角色直接交付，保证 demo 可跑完
            data = {"to": "user", "content": f"（{role} 离线产出）{str(raw)[:100]}",
                    "done": list(self.roles).index(role) == 0}
        done = bool(data.get("done", False)) and str(data.get("to", "")) == "user"
        return Message(sender=role, recipient=str(data.get("to", "ALL")),
                       content=str(data.get("content", "")),
                       kind="done" if done else "task")

    def run(self, goal: str):
        """返回 (final_answer, board, stop_reason)。"""
        board = Blackboard()
        board.post(Message("user", "ALL", goal))
        previous_round: set = set()
        stalled = 0
        for round_no in range(1, self.max_rounds + 1):
            board.round = round_no
            current_round: set = set()
            for role, duty in self.roles.items():
                message = self._speak(role, duty, goal, board)
                board.post(message)
                current_round.add((message.sender, message.recipient, message.content))
                if message.kind == "done":
                    return message.content, board, "done"
            # 整轮消息与上一轮完全相同 → 判定互相推诿 / 原地打转
            if current_round == previous_round:
                stalled += 1
                if stalled >= 2:
                    return "", board, "deadlock_detected"
            else:
                stalled = 0
            previous_round = current_round
        return "", board, "max_rounds"
