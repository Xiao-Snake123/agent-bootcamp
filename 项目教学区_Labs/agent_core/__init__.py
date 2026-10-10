"""agent_core：所有 Lab 共用的中央骨架（P0 起持续增长）。

本包提供 Agent 最小系统的稳定抽象：
- LLMClient：LLM 接入抽象（OpenAI 兼容云端 + 离线 Mock），内置成本护栏；
- Tool / ToolRegistry：工具基类与带校验/重试的分发器；
- Memory / BufferMemory：记忆抽象（P0 仅短期窗口）；
- Agent / Trajectory：最小 Agent Loop 与轨迹记录；
- Registry：通用能力模块登记（供 K5/K7/K8/K9/K11 后续挂载）。

设计原则见 design_docs/03 §2：接口稳定、模块可插拔、本地优先。
"""

from .llm import LLMClient, OpenAIClient, MockLLMClient, CostLimitError, Usage
from .tools import Tool, Observation, ToolRegistry, ToolError
from .memory import Memory, BufferMemory
from .agent import Agent, Trajectory, Step
from .registry import Registry

__all__ = [
    "LLMClient", "OpenAIClient", "MockLLMClient", "CostLimitError", "Usage",
    "Tool", "Observation", "ToolRegistry", "ToolError",
    "Memory", "BufferMemory",
    "Agent", "Trajectory", "Step",
    "Registry",
]
