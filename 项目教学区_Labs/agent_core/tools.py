"""工具基类、工具注册表，以及带参数校验/重试的分发器。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Observation:
    """动作执行后的观察结果。ok=False 表示执行未成功（不中断循环，由 Agent 决定后续）。"""
    content: str
    ok: bool = True


class ToolError(Exception):
    """工具自身抛出的错误。"""


class Tool(ABC):
    """所有工具必须继承此类并填写 name/description/schema，实现 run()。"""

    name: str = ""
    description: str = ""
    schema: dict = field(default_factory=dict)  # {"properties": {"参数名": "类型描述"}}

    @abstractmethod
    def run(self, **kwargs) -> Observation:
        ...


class ToolRegistry:
    """登记工具并提供校验/重试分发。"""

    def __init__(self):
        self._tools = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def list(self):
        return list(self._tools.values())

    def dispatch(self, name: str, args: dict, retries: int = 1) -> Observation:
        """执行工具：先按 schema 清洗参数，失败重试，最终失败返回 ok=False 的观察。"""
        if name not in self._tools:
            return Observation(content=f"未知工具：{name}", ok=False)
        tool = self._tools[name]
        allowed = tool.schema.get("properties", {}) if tool.schema else {}
        clean = {k: v for k, v in args.items() if k in allowed} if allowed else dict(args)
        for attempt in range(retries + 1):
            try:
                return tool.run(**clean)
            except Exception as e:  # 教学场景不引入复杂退避
                if attempt == retries:
                    return Observation(content=f"工具 {name} 执行失败：{e}", ok=False)
        return Observation(content=f"工具 {name} 执行失败", ok=False)
