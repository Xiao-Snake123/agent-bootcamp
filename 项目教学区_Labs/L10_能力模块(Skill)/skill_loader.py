"""L10 Skill 加载器：注册/路由/按需加载，把真实 Skill（tutorial/code/skill_demo）注入 Agent。

对应 K10 的 Skill 封装层：Skill = 提示片段 + 绑定工具 + 步骤模板；lazy loading
只在匹配任务时注入，避免常驻污染上下文（呼应 K2 lost-in-the-middle）。
"""

import importlib
import os
import re
import sys

from agent_core.agent import Agent
from agent_core.tools import Tool, Observation


class Skill:
    def __init__(self, name, description, triggers, prompt, tool):
        self.name = name
        self.description = description
        self.triggers = triggers      # list[str]
        self.prompt = prompt          # 注入 Agent 的提示片段
        self.tool = tool              # 绑定工具（Tool 或 None）


class _SkillTool(Tool):
    def __init__(self, name, handler_fn):
        self.name = name
        self.description = "Skill 绑定工具"
        self.schema = {"properties": {}}
        self._fn = handler_fn

    def run(self, **kwargs) -> Observation:
        try:
            return Observation(content=self._fn(**kwargs))
        except Exception as e:
            return Observation(content=f"Skill 工具失败：{e}", ok=False)


class SkillRegistry:
    def __init__(self):
        self.skills = []

    def register(self, skill: Skill):
        self.skills.append(skill)

    def match(self, task: str) -> Skill | None:
        """按触发词路由：命中则返回 Skill（发现），否则 None。"""
        for s in self.skills:
            if any(trig in task for trig in s.triggers):
                return s
        return None

    def load_from_dir(self, skill_dir: str) -> Skill:
        """从 tutorial/code/skill_demo 这类目录加载真实 Skill。
        解析 SKILL.md frontmatter（name/description/triggers）+ 动态导入 handler。
        """
        meta_path = os.path.join(skill_dir, "SKILL.md")
        text = open(meta_path, encoding="utf-8").read()
        fm = re.search(r"^---\n(.*?)\n---", text, re.S).group(1)
        meta, key, buf, val = {}, None, [], ""
        for line in fm.splitlines():
            if line.startswith("  - "):
                buf.append(line[4:].strip())
            else:
                if key is not None:
                    meta[key] = buf if buf else val
                if ":" in line:
                    key, val = line.split(":", 1)
                    key, val = key.strip(), val.strip()
                    buf = []
                    if val:
                        meta[key] = val
                        key = None
        if key is not None:
            meta[key] = buf if buf else val
        if skill_dir not in sys.path:
            sys.path.insert(0, skill_dir)
        handler = importlib.import_module("handler")
        tool = _SkillTool("skill_search", handler.search)
        body = text.split("---", 2)[-1].strip()
        skill = Skill(meta.get("name", "skill"), meta.get("description", ""),
                      meta.get("triggers", []), body, tool)
        self.register(skill)
        return skill


def apply_to_agent(skill: Skill, agent: Agent):
    """按需加载（lazy loading）：注入提示片段 + 注册绑定工具。"""
    agent.system = (agent.system + "\n" + skill.prompt).strip()
    if skill.tool is not None:
        agent.tools.register(skill.tool)
