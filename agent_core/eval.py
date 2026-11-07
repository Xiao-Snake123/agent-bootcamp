"""评测与可观测（第 10 章）：基于 Trajectory 的离线评测。

对应 content_outline.md 第 10 章锚点「eval.py（新增），复用 Trajectory」。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvalCase:
    goal: str
    keywords: list = field(default_factory=list)
    forbidden_tools: list = field(default_factory=list)
    max_steps: int = 10


@dataclass
class EvalResult:
    goal: str
    passed: bool
    score: float
    checks: dict = field(default_factory=dict)


class TrajectoryEvaluator:
    """把「轨迹是否健康」拆成可解释的检查项，而不是只看最终答案。"""

    def evaluate(self, answer: str, trajectory, case: EvalCase) -> EvalResult:
        text = answer or ""
        keywords = case.keywords or []
        hit = sum(1 for k in keywords if k.lower() in text.lower())
        used = [s.action.get("name", "") for s in trajectory.tool_calls]

        checks = {
            "answered": bool(text.strip()) and not text.startswith("（"),
            "keywords": (hit / len(keywords)) if keywords else 1.0,
            "terminated": trajectory.stop_reason == "final",
            "no_forbidden_tools": not any(t in case.forbidden_tools for t in used),
            "tools_ok": len(trajectory.failed_calls) == 0,
            "efficient": len(trajectory.steps) <= case.max_steps,
        }
        weights = {"answered": 0.25, "keywords": 0.25, "terminated": 0.2,
                   "no_forbidden_tools": 0.1, "tools_ok": 0.1, "efficient": 0.1}
        score = sum(weights[k] * (float(v) if isinstance(v, bool) else v)
                    for k, v in checks.items())
        passed = (checks["answered"] and checks["terminated"] and checks["tools_ok"]
                  and checks["no_forbidden_tools"] and score >= 0.7)
        return EvalResult(goal=case.goal, passed=passed, score=round(score, 3),
                          checks=checks)

    def run_suite(self, cases: list, agent, max_steps: int = 10) -> list:
        results = []
        for case in cases:
            answer, trajectory = agent.run(case.goal, max_steps=max_steps)
            results.append(self.evaluate(answer, trajectory, case))
        return results

    @staticmethod
    def report(results: list) -> str:
        lines = [f"评测 {len(results)} 例，通过 {sum(r.passed for r in results)} 例"]
        for r in results:
            lines.append(f"  [{'PASS' if r.passed else 'FAIL'}] {r.score:.3f}  {r.goal[:40]}")
        return "\n".join(lines)
