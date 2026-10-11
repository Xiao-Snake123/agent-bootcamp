"""L06 验收：可执行反思判定正确/错误 + 自我修正能收敛。"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from reflector import Reflector
from self_correct_loop import SelfCorrectLoop


def test_reflector_accepts_valid_code():
    ok, fb = Reflector().reflect('print("ok")')
    assert ok is True


def test_reflector_rejects_bad_code():
    ok, fb = Reflector().reflect('print("oops')
    assert ok is False
    assert "SyntaxError" in fb


def test_self_correct_converges():
    def gen(goal, feedback):
        if feedback and "SyntaxError" in feedback:
            return 'print("hello")'
        return 'print("hello'

    draft, iters, fb = SelfCorrectLoop(gen, Reflector(), max_iter=3).run("x")
    assert iters == 2
    assert draft == 'print("hello")'
