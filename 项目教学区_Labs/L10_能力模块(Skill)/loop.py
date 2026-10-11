"""L10 演示：任务路由 → 按需 load_skill → 注入提示+工具 → Agent 行为变化（离线，无需 Key）。

运行：
    cd 项目教学区_Labs/L10_能力模块(Skill)
    python loop.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
_BOOTCAMP = os.path.dirname(_PARENT)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_core.llm import MockLLMClient
from agent_core.agent import Agent
from agent_core.tools import ToolRegistry
from skill_loader import SkillRegistry, apply_to_agent


class SkillMock(MockLLMClient):
    def complete(self, messages, **kwargs):
        user = next((m["content"] for m in messages if m.get("role") == "user"), "")
        obs = [m["content"] for m in messages if m.get("role") == "tool"]
        if obs:
            return '{"final_answer": "据 Skill 检索：' + obs[-1] + '"}'
        if any(k in user for k in ("检索", "查资料", "知识库", "找文档")):
            return '{"action": "skill_search", "args": {"query": "RAG"}}'
        return '{"final_answer": "(基础 Agent) ' + user + '"}'


def demo():
    skill_dir = os.path.join(_BOOTCAMP, "tutorial", "code", "skill_demo")
    reg = SkillRegistry()
    reg.load_from_dir(skill_dir)
    s = reg.skills[0]
    print(f"已注册 Skill: {s.name} | 触发词: {s.triggers}")

    # 任务1：匹配 → 加载 Skill，注入提示+工具，行为变化
    agent = Agent(llm=SkillMock(), tools=ToolRegistry())
    match = reg.match("帮我查资料：RAG 是什么")
    if match:
        apply_to_agent(match, agent)
        print("任务1 匹配到 Skill，已注入提示；system 含 Skill 提示:", "doc-search" in agent.system)
    final, _ = agent.run("帮我查资料：RAG 是什么", max_steps=4)
    print("任务1 最终:", final)

    # 任务2：不匹配 → 不加载，不占上下文，基础 Agent 处理
    agent2 = Agent(llm=SkillMock(), tools=ToolRegistry())
    m2 = reg.match("今天天气如何")
    print("任务2 是否匹配 Skill（应为 False）:", m2 is not None)
    final2, _ = agent2.run("今天天气如何", max_steps=4)
    print("任务2 最终:", final2)


if __name__ == "__main__":
    demo()
