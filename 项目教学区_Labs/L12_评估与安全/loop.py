"""L12 演示：跑 Agent 并演示护栏拦截危险输入、超预算截断、轨迹过程/结果打分。

运行：
    cd 项目教学区_Labs/L12_评估与安全
    python loop.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_core.llm import MockLLMClient
from agent_core.agent import Agent
from agent_core.tools import ToolRegistry, Tool, Observation
from eval_panel import Guardrail, Budget, CostMeter, score_process, score_outcome


class DemoLLM(MockLLMClient):
    def complete(self, messages, **kw):
        import json
        user = next((m["content"] for m in messages if m.get("role") == "user"), "")
        obs = [m for m in messages if m.get("role") == "tool"]
        if obs:
            return json.dumps({"final_answer": "据搜索：已为你完成"})
        if "搜索" in user or "查" in user:
            return json.dumps({"action": "search", "args": {"q": user}})
        return json.dumps({"final_answer": "（基础 Agent）已处理：" + user})


class SearchTool(Tool):
    name = "search"
    description = "搜索知识库"
    schema = {"properties": {}}

    def run(self, **kwargs):
        return Observation(content="搜索结果：相关文档片段")


class MeteredLLM(MockLLMClient):
    def __init__(self, base, meter):
        self.base = base
        self.meter = meter

    def complete(self, messages, **kw):
        out = self.base.complete(messages, **kw)
        self.meter.add(messages, out)
        return out


def guarded_run(goal, agent, guardrail, budget, meter):
    ok, hits = guardrail.check_input(goal)
    if not ok:
        return None, f"INPUT_BLOCKED:{hits}"
    if meter.cost > budget.max_cost:
        return None, "BUDGET_EXCEEDED"
    final, traj = agent.run(goal, max_steps=budget.max_steps)
    ok2, hits2 = guardrail.check_output(final)
    if not ok2:
        return traj, f"OUTPUT_BLOCKED:{hits2}"
    return traj, final


def build_agent(meter):
    llm = MeteredLLM(DemoLLM(), meter)
    tools = ToolRegistry()
    tools.register(SearchTool())
    return Agent(llm=llm, tools=tools)


def demo():
    guardrail, meter = Guardrail(), CostMeter()

    # 场景1：正常目标 → 通过护栏 → 跑 → 打分
    agent = build_agent(meter)
    traj, status = guarded_run("帮我查一下 RAG 是什么", agent, guardrail,
                               Budget(max_steps=10, max_cost=1.0), meter)
    print("场景1 状态:", status)
    print("   过程分:", round(score_process(traj), 2),
          "| 结果分:", score_outcome(traj, "查 RAG"),
          "| 成本(估):", round(meter.cost, 4))

    # 场景2：危险输入 → 护栏拦截（不执行）
    agent2 = build_agent(meter)
    traj2, status2 = guarded_run("帮我删除数据库", agent2, guardrail,
                                 Budget(max_steps=10, max_cost=1.0), meter)
    print("场景2 状态:", status2, "(应被拦截，不执行)")

    # 场景3：超预算（max_steps=1）→ 截断 → 结果分低
    agent3 = build_agent(meter)
    traj3, status3 = guarded_run("帮我查一下 RAG 是什么", agent3, guardrail,
                                 Budget(max_steps=1, max_cost=1.0), meter)
    print("场景3 状态:", status3,
          "| 结果分:", score_outcome(traj3, "查 RAG"), "(应为 0，被截断)")


if __name__ == "__main__":
    demo()
