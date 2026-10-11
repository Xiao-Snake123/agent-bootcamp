"""L10 验收：路由匹配、不匹配返回 None、按需注入提示+工具。"""

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


def _skill_dir():
    return os.path.join(_BOOTCAMP, "tutorial", "code", "skill_demo")


def test_registry_matches_trigger():
    reg = SkillRegistry()
    reg.load_from_dir(_skill_dir())
    assert reg.match("帮我检索资料") is not None
    assert reg.match("今天天气怎么样") is None


def test_apply_injects_prompt_and_tool():
    reg = SkillRegistry()
    skill = reg.load_from_dir(_skill_dir())
    agent = Agent(llm=MockLLMClient(), tools=ToolRegistry())
    apply_to_agent(skill, agent)
    assert "doc-search" in agent.system                 # 提示片段注入
    assert "skill_search" in [t.name for t in agent.tools.list()]  # 绑定工具注册


def test_lazy_loading_no_inject_when_unmatched():
    reg = SkillRegistry()
    reg.load_from_dir(_skill_dir())
    agent = Agent(llm=MockLLMClient(), tools=ToolRegistry())
    assert reg.match(" unrelated task ") is None
    assert agent.tools.list() == []                    # 不匹配则不加载，不占上下文
