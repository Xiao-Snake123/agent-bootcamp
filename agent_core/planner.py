"""规划与分解（第 4 章）：Plan-and-Execute + 依赖 DAG + 失败重规划。

对应 content_outline.md 第 4 章锚点「planner 模块（新增）」。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ._util import extract_json


@dataclass
class PlanStep:
    id: str
    description: str
    depends_on: list = field(default_factory=list)
    status: str = "pending"      # pending / running / done / failed
    output: str = ""


@dataclass
class Plan:
    goal: str
    steps: list = field(default_factory=list)

    @property
    def done(self):
        return [s for s in self.steps if s.status == "done"]

    @property
    def failed(self):
        return [s for s in self.steps if s.status == "failed"]

    def summary(self) -> str:
        return "\n".join(
            f"  [{s.status:>7}] {s.id}: {s.description}"
            + (f"  -> {s.output[:60]}" if s.output else "")
            for s in self.steps)


class Planner:
    """LLM 生成计划，拓扑调度执行，失败时让 LLM 重规划剩余步骤。"""

    def __init__(self, llm):
        self.llm = llm

    def make_plan(self, goal: str, max_steps: int = 5) -> Plan:
        prompt = (
            f"把下面的目标分解为不超过 {max_steps} 个可执行子步骤。\n"
            '只输出 JSON 数组，形如：'
            '[{"id":"s1","description":"做什么","depends_on":[]},'
            ' {"id":"s2","description":"做什么","depends_on":["s1"]}]\n'
            f"目标：{goal}")
        raw = self.llm.complete([
            {"role": "system", "content": "你是任务规划器，只输出 JSON，不要解释。"},
            {"role": "user", "content": prompt},
        ])
        data = extract_json(raw)
        if isinstance(data, dict):
            data = data.get("steps", [])
        steps = []
        if isinstance(data, list):
            for i, item in enumerate(data[:max_steps]):
                if isinstance(item, str):
                    item = {"description": item}
                if not isinstance(item, dict):
                    continue
                steps.append(PlanStep(
                    id=str(item.get("id", f"s{i + 1}")),
                    description=str(item.get("description", "")),
                    depends_on=[str(d) for d in item.get("depends_on", [])]))
        if not steps:  # 离线 Mock / 模型未给 JSON 时退化为单步，保证 demo 可跑
            steps = [PlanStep(id="s1", description=goal)]
        return Plan(goal=goal, steps=steps)

    def runnable(self, plan: Plan) -> list:
        done = {s.id for s in plan.done}
        return [s for s in plan.steps
                if s.status == "pending" and all(d in done for d in s.depends_on)]

    def replan(self, plan: Plan, failed: list) -> Plan:
        """保留已完成步骤，让 LLM 给出替代步骤（最多调用一次，防无限重规划）。"""
        context = "\n".join(f"{s.id}: {s.description} -> {s.output}" for s in plan.done)
        reason = "; ".join(f"{s.id} 失败：{s.output}" for s in failed)
        prompt = (f"目标：{plan.goal}\n已完成：\n{context}\n失败：{reason}\n"
                  "请给出替代步骤，只输出 JSON 数组（id 用 r1, r2...，"
                  "depends_on 引用已完成步骤的 id）。")
        raw = self.llm.complete([
            {"role": "system", "content": "你是任务规划器，只输出 JSON。"},
            {"role": "user", "content": prompt}])
        data = extract_json(raw)
        steps = []
        if isinstance(data, list):
            for i, item in enumerate(data[:3]):
                if isinstance(item, str):
                    item = {"description": item}
                if isinstance(item, dict):
                    steps.append(PlanStep(id=str(item.get("id", f"r{i + 1}")),
                                          description=str(item.get("description", "")),
                                          depends_on=[str(d) for d in item.get("depends_on", [])]))
        if not steps:
            steps = [PlanStep(id="r1", description="；".join(s.description for s in failed))]
        return Plan(goal=plan.goal, steps=steps)

    def execute(self, plan: Plan, run_step, max_replans: int = 1) -> Plan:
        """按拓扑序执行；run_step(step) -> str，抛异常视为失败。"""
        replans, guard = 0, 0
        while guard < 100:
            guard += 1
            batch = self.runnable(plan)
            if not batch:
                if not [s for s in plan.steps if s.status == "pending"]:
                    break
                # 依赖指向不存在/失败节点 → 剪掉无效依赖，避免死锁
                done = {s.id for s in plan.done}
                for s in plan.steps:
                    if s.status == "pending":
                        s.depends_on = [d for d in s.depends_on if d in done]
                continue
            for step in batch:
                step.status = "running"
                try:
                    step.output = str(run_step(step))
                    step.status = "done"
                except Exception as e:
                    step.output = f"失败：{e}"
                    step.status = "failed"
            failed = plan.failed
            if not failed:
                continue
            if replans < max_replans:
                replans += 1
                plan.steps = plan.done + self.replan(plan, failed).steps
            else:
                break
        return plan
