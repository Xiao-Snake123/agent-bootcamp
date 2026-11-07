"""反思与自修正（第 5 章）：Reflexion 循环。

复用 Agent 的 Trajectory，基于客观轨迹生成反思，把经验注入下一轮重试。
对应 content_outline.md 第 5 章锚点「reflector 模块（新增）」。
"""
from __future__ import annotations

from dataclasses import dataclass

from ._util import extract_json


@dataclass
class Reflection:
    critique: str
    lesson: str
    should_retry: bool


class Reflector:
    """基于轨迹的反思器；should_retry=False 或达到上限即停止，防无限循环。"""

    def __init__(self, llm, max_retries: int = 2):
        self.llm = llm
        self.max_retries = max_retries

    @staticmethod
    def transcript(trajectory) -> str:
        lines = [f"[{i + 1}] {s.action.get('name')}({s.action.get('args')}) "
                 f"-> {s.observation[:120]} (ok={s.ok})"
                 for i, s in enumerate(trajectory.steps)]
        return "\n".join(lines) or "（无工具调用）"

    def reflect(self, goal: str, trajectory) -> Reflection:
        prompt = (
            f"目标：{goal}\n终止原因：{trajectory.stop_reason}\n"
            f"轨迹：\n{self.transcript(trajectory)}\n"
            f"最终答案：{trajectory.final_answer}\n"
            '请输出 JSON：{"critique":"哪里做错了","lesson":"下一轮必须怎么改",'
            '"should_retry":true/false}。只有轨迹客观失败或答案明显未达成目标时才重试。')
        raw = self.llm.complete([
            {"role": "system", "content": "你是严格的 Agent 复盘器，只输出 JSON。"},
            {"role": "user", "content": prompt}])
        data = extract_json(raw)
        if not isinstance(data, dict):
            # 离线 Mock 或模型未给 JSON：默认不重试，避免空转烧钱
            return Reflection(critique="（无结构化反思）", lesson=str(raw)[:120],
                              should_retry=False)
        return Reflection(
            critique=str(data.get("critique", "")),
            lesson=str(data.get("lesson", "")),
            should_retry=bool(data.get("should_retry", False)),
        )

    def run(self, agent, goal: str, max_steps: int = 10):
        """返回 (answer, last_trajectory, reflections)。"""
        reflections = []
        lesson = ""
        answer, trajectory = "", None
        for attempt in range(self.max_retries + 1):
            effective = goal if not lesson else f"{goal}\n\n上轮复盘经验（务必避免重犯）：{lesson}"
            answer, trajectory = agent.run(effective, max_steps=max_steps)
            reflection = self.reflect(goal, trajectory)
            reflections.append(reflection)
            if not reflection.should_retry:
                break
            lesson = reflection.lesson
        return answer, trajectory, reflections
