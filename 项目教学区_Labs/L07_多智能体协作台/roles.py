"""L07 角色：Researcher / Writer / Critic 三角色（离线 mock，无需 LLM）。

每个 Role 读 message bus 的历史、基于必要上下文产出自家输出并发布。
角色解耦、专业化——对应 K7 的 role 概念；Critic 与 Actor 分离也减少自评偏见（呼应 K6）。
"""

from abc import ABC, abstractmethod

from message_bus import MessageBus


class Role(ABC):
    name: str = ""

    @abstractmethod
    def act(self, bus: MessageBus) -> str:
        ...


class Researcher(Role):
    name = "Researcher"

    def act(self, bus: MessageBus) -> str:
        topic = bus.topic
        out = f"[研究要点] 关于《{topic}》：1)定义 2)2025前沿 3)风险与误区"
        bus.post(self.name, out)
        return out


class Writer(Role):
    name = "Writer"

    def act(self, bus: MessageBus) -> str:
        brief = bus.last_from("Researcher")
        out = f"[文稿] 基于「{brief}」撰写正文：本文先界定概念，再梳理前沿进展，最后提示风险。"
        bus.post(self.name, out)
        return out


class Critic(Role):
    name = "Critic"

    def act(self, bus: MessageBus) -> str:
        # 离线规则：首次评审要求补充风险段；第二次（已有修改）给通过——
        # 演示"评审循环"在 Orchestrator 驱动下收敛（K7 评审拓扑）。
        prior_reviews = [c for r, c in bus.history if r == self.name]
        draft = bus.last_from("Writer")
        if prior_reviews:
            out = "[评审] 通过：结构完整，已覆盖风险段。"
        else:
            out = "[评审] 需修改：请补充风险段后再提交。"
        bus.post(self.name, out)
        return out
