"""L06 演示：含错代码 → 可执行反思(compile) → 修正通过（离线，无需 Key）。

运行：
    cd 项目教学区_Labs/L06_反思与自评
    python loop.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from reflector import Reflector
from self_correct_loop import SelfCorrectLoop


def mock_generator(goal, feedback):
    """离线生成器：首轮故意语法错；收到 SyntaxError 反馈后产出正确版。"""
    if feedback and "SyntaxError" in feedback:
        return 'print("hello, world")'   # 修正版（合法）
    return 'print("hello'                # 缺右引号，语法错


def demo():
    print("=== 自我修正循环（可执行反思：compile 校验）===")
    loop = SelfCorrectLoop(mock_generator, Reflector(), max_iter=3)
    draft, iters, fb = loop.run("写一句打印 hello 的代码")
    print(f"  收敛轮数: {iters}")
    print(f"  最终代码: {draft}")
    print(f"  反思结论: {fb}")


if __name__ == "__main__":
    demo()
