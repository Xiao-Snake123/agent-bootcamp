"""L05 规划器：把目标拆成可执行的子目标列表（Plan-and-Execute 的"规划"阶段）。

规划与执行解耦——本文件只负责"想清楚要做什么"，执行交给 executor.py。
真实实现让 LLM 担任 planner（见 K5），产出带可验证产出的步骤；本 Lab 用
离线 MockPlanner 把规则化目标拆成子目标，无需任何 API Key。
"""

from abc import ABC, abstractmethod


class Planner(ABC):
    @abstractmethod
    def plan(self, goal: str) -> list:
        """返回子目标/步骤的有序列表（文本）。"""
        ...


class MockPlanner(Planner):
    """离线规划器：按简单规则产出子目标。

    - 含"并/然后"的复合目标 → 拆成多步；
    - 否则 → 给"理解/执行/复核"通用三步（保证子目标可验证的雏形）。
    """

    def plan(self, goal: str) -> list:
        if "并" in goal or "然后" in goal:
            parts = [p.strip() for p in goal.replace("然后", "并").split("并") if p.strip()]
            return parts
        return [f"理解目标：{goal}", f"执行：{goal}", f"复核结果：{goal}"]
