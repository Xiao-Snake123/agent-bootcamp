"""L07 编排者：路由角色、串联流水线、驱动评审循环、负责终止。

对应 K7 的 orchestrator：决定"谁在何时行动"、把产出 handoff 给下一角色、
用 max_rounds / "通过"信号作为终止条件（陷阱②无终止条件）。
"""

from message_bus import MessageBus
from roles import Researcher, Writer, Critic


class Orchestrator:
    def __init__(self, bus: MessageBus, max_rounds: int = 3):
        self.bus = bus
        self.max_rounds = max_rounds
        # 固定三角色：研究员→写手→评审（流水线 + 评审循环）
        self.researcher = Researcher()
        self.writer = Writer()
        self.critic = Critic()

    def run(self, topic: str):
        self.bus.topic = topic
        # 流水线阶段：先研究、再写初稿
        self.researcher.act(self.bus)
        self.writer.act(self.bus)
        # 评审循环：Critic 评审，未通过则 Writer 重修，直到通过或上限
        for _ in range(self.max_rounds):
            verdict = self.critic.act(self.bus)
            if "通过" in verdict:
                break
            self.writer.act(self.bus)
        return self.bus.all()
