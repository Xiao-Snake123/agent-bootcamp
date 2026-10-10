"""通用能力模块注册表。

后续 Lab（K5 规划、K7 反思、K8 多智能体、K9 RAG、K11 评估…）会把各自的能力
模块（Planner / Reflector / Retriever / Evaluator …）注册到这里，由 Agent 组合调用。
与 tools.py 里的 ToolRegistry 不同：这里不绑定"工具执行"，只做 name→对象 的登记。
"""


class Registry:
    def __init__(self):
        self._items = {}

    def register(self, name: str, obj):
        self._items[name] = obj

    def get(self, name: str):
        if name not in self._items:
            raise KeyError(f"未注册的模块：{name}")
        return self._items[name]

    def list_names(self):
        return list(self._items.keys())
