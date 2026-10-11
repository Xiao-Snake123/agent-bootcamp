"""L07 消息总线：多角色之间解耦传递消息的媒介。

角色读历史、产出自家输出并发布；彼此不直接耦合，由 orchestrator 驱动。
对应 K7 的 message bus 概念——避免"各角色上下文互灌爆炸"（陷阱③）。
"""


class MessageBus:
    def __init__(self, topic: str = ""):
        self.topic = topic
        self.history = []   # list of (role, content)

    def post(self, role: str, content: str):
        self.history.append((role, content))

    def last_from(self, role: str) -> str:
        for r, c in reversed(self.history):
            if r == role:
                return c
        return ""

    def all(self):
        return list(self.history)
