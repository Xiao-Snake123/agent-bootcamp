"""L04 记忆工具：把长期记忆暴露成 Agent 可调用的工具（agentic memory 接口）。

SaveFact / Recall 两个工具让 Agent 在运行时显式"写/读"长期记忆，
而不是靠工程师把对话全塞进上下文——这正是 K4 与"只堆上下文"的本质区别。
"""

from agent_core.tools import Tool, Observation
from agent_core.memory import LongTermMemory


class SaveFactTool(Tool):
    name = "SaveFact"
    description = "把一条事实写入长期记忆（key-value），供后续跨会话召回。"
    schema = {"properties": {"key": "事实键，如 user_name", "value": "事实值，如 小明"}}

    def __init__(self, memory: LongTermMemory):
        self.memory = memory

    def run(self, key: str, value: str) -> Observation:
        self.memory.save_fact(key, value)
        return Observation(content=f"已保存 {key}={value}")


class RecallTool(Tool):
    name = "Recall"
    description = "从长期记忆取回某 key 的事实；查不到返回空。"
    schema = {"properties": {"key": "要回忆的事实键，如 user_name"}}

    def __init__(self, memory: LongTermMemory):
        self.memory = memory

    def run(self, key: str) -> Observation:
        v = self.memory.recall(key)
        return Observation(content=v if v else "（未找到该记忆）")
