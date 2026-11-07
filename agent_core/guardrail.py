"""安全与合规（第 11 章）：提示注入检测 + 最小权限 + 输出泄露防护。

对应 content_outline.md 第 11 章锚点「guardrail 模块（新增）」。
"""
from __future__ import annotations

import re

from .tools import Observation, ToolRegistry

INJECTION_PATTERNS = [
    r"忽略(之前|上面|以上|所有).{0,8}(指令|提示|规则)",
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"(输出|打印|复述|泄露).{0,8}(系统提示|system\s*prompt|内部指令)",
    r"reveal\s+(your\s+)?system\s+prompt",
    r"你现在是.{0,12}(不受限制|无限制|开发者模式|DAN)",
]
DANGEROUS_ARG_PATTERNS = [
    r"rm\s+-rf", r"__import__", r"os\.system", r"subprocess",
    r"eval\(", r"exec\(", r"\.\./\.\./",
]


class Guardrail:
    """三道检查：输入 / 工具调用 / 输出。"""

    def __init__(self, allowed_tools: list | None = None,
                 system_prompt: str = "", extra_deny: list | None = None):
        self.allowed_tools = set(allowed_tools) if allowed_tools is not None else None
        self.system_prompt = system_prompt
        self.deny = list(extra_deny or [])
        self.events: list = []

    def _log(self, stage: str, allowed: bool, reason: str):
        self.events.append({"stage": stage, "allowed": allowed, "reason": reason})

    def check_input(self, text: str):
        for pattern in INJECTION_PATTERNS + self.deny:
            if re.search(pattern, text or "", re.I):
                reason = f"疑似提示注入（匹配 {pattern}）"
                self._log("input", False, reason)
                return False, reason
        self._log("input", True, "")
        return True, ""

    def check_tool_call(self, name: str, args: dict):
        if self.allowed_tools is not None and name not in self.allowed_tools:
            reason = f"最小权限：{name} 不在白名单 {sorted(self.allowed_tools)}"
            self._log("tool", False, reason)
            return False, reason
        blob = f"{name} {args}"
        for pattern in DANGEROUS_ARG_PATTERNS:
            if re.search(pattern, blob, re.I):
                reason = f"危险参数（匹配 {pattern}）"
                self._log("tool", False, reason)
                return False, reason
        self._log("tool", True, "")
        return True, ""

    def check_output(self, text: str):
        if self.system_prompt and self.system_prompt[:40] in (text or ""):
            reason = "输出疑似包含系统提示"
            self._log("output", False, reason)
            return False, reason
        self._log("output", True, "")
        return True, ""


class GuardedToolRegistry(ToolRegistry):
    """在分发前插入工具级护栏；被拦截时返回 ok=False 观察而非抛异常。"""

    def __init__(self, guardrail: Guardrail):
        super().__init__()
        self.guardrail = guardrail
        self.blocked: list = []

    def dispatch(self, name: str, args: dict, retries: int = 1) -> Observation:
        allowed, reason = self.guardrail.check_tool_call(name, args)
        if not allowed:
            self.blocked.append((name, reason))
            return Observation(f"护栏拦截：{reason}", ok=False)
        return super().dispatch(name, args, retries)


def guard_agent(agent, guardrail: Guardrail):
    """给已有 Agent 套输入/输出护栏，返回包装后的 run。"""
    original = agent.run

    def run(goal: str, max_steps: int = 10):
        allowed, reason = guardrail.check_input(goal)
        if not allowed:
            from .agent import Trajectory
            return f"输入被护栏拦截：{reason}", Trajectory(stop_reason="guardrail")
        answer, trajectory = original(goal, max_steps)
        ok, reason = guardrail.check_output(answer)
        if not ok:
            answer = f"输出被护栏拦截：{reason}"
            trajectory.stop_reason = "guardrail"
        return answer, trajectory

    return run
