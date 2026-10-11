"""L03 演示工具：天气查询 + 计算器 + 搜索，带 JSON-Schema 参数。"""

import re
from agent_core.tools import Tool, Observation


class WeatherTool(Tool):
    name = "get_weather"
    description = "查询某城市的当前天气，参数为城市名，如：北京"
    schema = {"type": "object", "properties": {"city": "string"}, "required": ["city"]}

    def run(self, city: str) -> Observation:
        data = {"北京": "晴 22℃", "上海": "多云 25℃", "广州": "雷阵雨 28℃"}
        return Observation(content=data.get(city, f"{city} 天气未知"))


class CalculatorTool(Tool):
    name = "calculator"
    description = "计算四则运算表达式，如 23*17"
    schema = {"type": "object", "properties": {"expr": "string"}, "required": ["expr"]}

    def run(self, expr: str) -> Observation:
        if not re.fullmatch(r"[0-9+\-*/().\s]+", expr or ""):
            return Observation(content="非法表达式（仅允许数字与 +-*/().）", ok=False)
        try:
            result = eval(expr, {"__builtins__": {}}, {})
        except Exception as e:
            return Observation(content=f"计算出错：{e}", ok=False)
        return Observation(content=str(result))


class SearchTool(Tool):
    name = "get_search"
    description = "搜索公开资料，参数为查询关键词，如：人工智能 最新进展"
    schema = {"type": "object", "properties": {"query": "string"}, "required": ["query"]}

    def run(self, query: str) -> Observation:
        data = {
            "人工智能": "AI 是模拟智能行为的技术总称，含机器学习与深度学习。",
            "机器学习": "ML 是从数据中自动学习规律的一类方法。",
        }
        for k, v in data.items():
            if k in (query or ""):
                return Observation(content=v)
        return Observation(content=f"（Mock）未收录：{query}")
