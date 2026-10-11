"""L06 反思器：对产出做"可执行反馈"式反思（比纯语言反思可靠）。

本 Lab 用 Python compile 真实校验代码语法——这是 K6 强调的"可执行验证"，
而非让模型嘴上说"我改好了"（陷阱②自我欺骗）。
"""

import io  # 保留 import 位，便于将来扩展到捕获 stdout/stderr


class Reflector:
    def reflect(self, code: str):
        """返回 (ok: bool, feedback: str)。用真实编译做可执行反思。"""
        try:
            compile(code, "<agent>", "exec")
            return True, "语法正确，通过。"
        except SyntaxError as e:
            return False, f"SyntaxError: {e.msg} (行 {e.lineno}, 列 {e.offset})"
        except Exception as e:  # 其他编译期异常
            return False, f"编译期异常: {e}"
