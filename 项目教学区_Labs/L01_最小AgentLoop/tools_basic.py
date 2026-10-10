"""L01 的基础工具：计算器。被 loop.py 与 test_loop.py 共用。"""

import re
from agent_core.tools import Tool, Observation


class CalculatorTool(Tool):
    """四则运算计算器。用白名单正则限制输入，避免任意代码执行。"""

    name = "calculator"
    description = "计算四则运算表达式，如 23*17"
    schema = {"properties": {"expr": "string"}}

    def run(self, expr: str) -> Observation:
        if not re.fullmatch(r"[0-9+\-*/().\s]+", expr or ""):
            return Observation(content="非法表达式（仅允许数字与 +-*/().）", ok=False)
        try:
            # 禁用内置命名空间，仅做纯算术求值
            result = eval(expr, {"__builtins__": {}}, {})
        except Exception as e:
            return Observation(content=f"计算出错：{e}", ok=False)
        return Observation(content=str(result))
