"""L06 自我修正循环：生成 → 可执行反思 → 不通过则回填反馈再生成。

对应 K6 的反思闭环：靠"可执行反馈"驱动修正，而非语言自查（破解自我欺骗）。
generator 是 callable(goal, feedback) -> draft，可替换成真 LLM。
"""


class SelfCorrectLoop:
    def __init__(self, generator, reflector, max_iter: int = 3):
        self.generator = generator   # 生成器：接收目标与上一轮反馈，产出 draft
        self.reflector = reflector   # 反思器：给出 (ok, feedback)
        self.max_iter = max_iter     # 收敛上限，防不收敛空转（陷阱①）

    def run(self, goal: str):
        feedback = ""
        draft = ""
        for i in range(self.max_iter):
            draft = self.generator(goal, feedback)
            ok, fb = self.reflector.reflect(draft)
            if ok:
                return draft, i + 1, fb
            feedback = fb   # 回填给生成器，下一轮据此修正
        return draft, self.max_iter, "（达到上限仍未通过）"
