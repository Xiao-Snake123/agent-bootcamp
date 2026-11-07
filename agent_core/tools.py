"""工具层（v2）：原生 Function Calling schema + 参数校验 + 重试分发。

保留 v1 的 Tool / ToolRegistry / Observation / ToolError 接口形状，
但 schema 升级为标准 JSON Schema，并提供 openai_schemas() 直接喂给 chat(tools=...)。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Observation:
    """动作执行后的观察。ok=False 表示失败但不中断循环，交回模型决策。"""
    content: str
    ok: bool = True


class ToolError(Exception):
    """工具自身抛出的错误。"""


@dataclass
class Tool:
    """一个工具：名称 / 描述 / JSON Schema 参数 / 处理函数。"""
    name: str
    description: str = ""
    parameters: dict = field(default_factory=lambda: {
        "type": "object", "properties": {}, "required": []})
    handler: Callable | None = None

    def run(self, **kwargs) -> Observation:
        if self.handler is None:
            raise ToolError(f"工具 {self.name} 未绑定 handler")
        out = self.handler(**kwargs)
        return out if isinstance(out, Observation) else Observation(str(out))

    def openai_schema(self) -> dict:
        return {"type": "function", "function": {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }}


def make_tool(name: str, description: str, parameters: dict, handler: Callable) -> Tool:
    return Tool(name=name, description=description,
                parameters=parameters, handler=handler)


def _type_ok(expected: str, value) -> bool:
    return {
        "string": lambda v: isinstance(v, str),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "boolean": lambda v: isinstance(v, bool),
        "array": lambda v: isinstance(v, list),
        "object": lambda v: isinstance(v, dict),
    }.get(expected, lambda v: True)(value)


class ToolRegistry:
    """登记工具，提供校验/重试分发与 OpenAI tools schema 导出。"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def list(self) -> list:
        return list(self._tools.values())

    def openai_schemas(self) -> list:
        return [t.openai_schema() for t in self._tools.values()]

    def dispatch(self, name: str, args: dict, retries: int = 1) -> Observation:
        """校验参数 → 执行 → 失败重试 → 最终失败返回 ok=False 的观察。"""
        if name not in self._tools:
            return Observation(f"未知工具：{name}，可用：{', '.join(self._tools)}", ok=False)
        clean, error = self._validate(self._tools[name], args or {})
        if error:
            return Observation(error, ok=False)
        last = ""
        for _ in range(retries + 1):
            try:
                return self._tools[name].run(**clean)
            except Exception as e:  # 教学场景不引入复杂退避
                last = str(e)
        return Observation(f"工具 {name} 执行失败：{last}", ok=False)

    @staticmethod
    def _validate(tool: Tool, args: dict):
        schema = tool.parameters or {}
        props = schema.get("properties", {})
        missing = [k for k in schema.get("required", []) if k not in args]
        if missing:
            return args, f"工具 {tool.name} 缺少必填参数：{', '.join(missing)}"
        for key, value in args.items():
            expected = props.get(key, {}).get("type") if key in props else None
            if expected and not _type_ok(expected, value):
                return args, f"工具 {tool.name} 参数 {key} 类型应为 {expected}，实得 {type(value).__name__}"
        clean = {k: v for k, v in args.items() if not props or k in props}
        return clean, None
