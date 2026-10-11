"""L12 评估与安全面板：护栏（输入/输出/预算）+ 成本计量 + 过程/结果评分。

对应 K12：把"可度量（评估）+ 可信任（护栏）"落到 K11 产出的 Trajectory 上。
纯 Python，无重依赖；评分接口可换成 LLM-as-judge。
"""

import re
from dataclasses import dataclass, field


# ---------------- 护栏 ----------------
class Guardrail:
    DANGER_INPUT = ["删除数据库", "rm -rf", "drop table", "格式化", "泄露密码", "泄露密钥"]
    LEAK_OUTPUT = [r"(api[_-]?key|sk-[a-z0-9]{8,}|密码[:：]\s*\S+|token[:：]\s*\S+)"]

    def check_input(self, text: str):
        hits = [k for k in self.DANGER_INPUT if k in text]
        return (len(hits) == 0, hits)

    def check_output(self, text: str):
        for pat in self.LEAK_OUTPUT:
            if re.search(pat, text or "", re.I):
                return (False, [f"疑似泄露: {pat}"])
        return (True, [])


@dataclass
class Budget:
    max_steps: int = 10
    max_cost: float = 1.0


# ---------------- 成本计量 ----------------
class CostMeter:
    def __init__(self):
        self.cost = 0.0
        self.calls = 0

    def add(self, messages, out):
        n = sum(len(str(m.get("content", ""))) for m in messages) + len(str(out))
        self.cost += n / 4 * 0.0001   # 粗略 token≈字符/4，单价占位
        self.calls += 1


# ---------------- 评分 ----------------
def score_process(traj) -> float:
    """过程级：每步是否有合理 thought + (action/observation)，且无失败/未知工具。"""
    steps = traj.steps
    if not steps:
        return 0.0
    good = 0
    for s in steps:
        if not s.thought:
            continue
        if s.action or s.observation:
            if "未知工具" not in s.observation and "失败" not in s.observation:
                good += 1
    return good / len(steps)


def score_outcome(traj, goal: str = "") -> float:
    """结果级：最终答案是否有效、是否回应目标。"""
    fa = traj.final_answer or ""
    if not fa or "未给出" in fa or "达到步数上限" in fa:
        return 0.0
    if goal and any(w in fa for w in ("据", "完成", "处理", "检索")):
        return 1.0
    return 0.5
