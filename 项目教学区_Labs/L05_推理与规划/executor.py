"""L05 执行器：按规划逐步执行（Plan-and-Execute 的"执行"阶段）。

与 ReAct（边想边做）不同，这里先有完整 plan，再逐子目标交给执行单元
（可是一个 Agent、一个工具或一个函数）。每步产出应可复核/可验证（见 K5）。
"""

from typing import Callable, List


class PlanExecutor:
    def __init__(self, step_fn: Callable[[str], str]):
        """step_fn: 单步执行单元，输入子目标文本，返回结果文本。"""
        self.step_fn = step_fn

    def run(self, plan: List[str]) -> List[str]:
        results = []
        for step in plan:
            res = self.step_fn(step)
            results.append(res)
        return results
