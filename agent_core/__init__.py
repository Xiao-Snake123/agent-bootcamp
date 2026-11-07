"""agent_core v2（重生版）——Agent 工程化统一接口。

对齐《核心机制篇》12 章：LLM / 工具 / 记忆 / Agent 主循环为基座，
planner / reflector / multi / retriever / orchestrator / eval / guardrail / registry
为各章配套模块；HTTP 封装见 ``agent_core.serve.create_app``（延迟导入，不强依赖 FastAPI）。

    from agent_core import build_llm, ToolRegistry, make_tool, Agent
"""
from .llm import (LLMClient, OpenAICompatibleClient, MockLLMClient,
                  ChatResponse, ToolCall, Usage, CostLimitError, tool_call)
from .tools import Tool, ToolRegistry, Observation, ToolError, make_tool
from .memory import Memory, BufferMemory, SummaryMemory, LongTermMemory
from .agent import Agent, Step, Trajectory
from .config import build_llm, auto_llm, load_env, get, default_budget
from .planner import Planner, Plan, PlanStep
from .reflector import Reflector, Reflection
from .multi import MultiAgent, Blackboard, Message
from .retriever import Indexer, HybridRetriever, Document, chunk_markdown
from .orchestrator import Graph, Node, once
from .eval import TrajectoryEvaluator, EvalCase, EvalResult
from .guardrail import Guardrail, GuardedToolRegistry, guard_agent
from .registry import Registry

__all__ = [
    "LLMClient", "OpenAICompatibleClient", "MockLLMClient",
    "ChatResponse", "ToolCall", "Usage", "CostLimitError", "tool_call",
    "Tool", "ToolRegistry", "Observation", "ToolError", "make_tool",
    "Memory", "BufferMemory", "SummaryMemory", "LongTermMemory",
    "Agent", "Step", "Trajectory",
    "build_llm", "auto_llm", "load_env", "get", "default_budget",
    "Planner", "Plan", "PlanStep", "Reflector", "Reflection",
    "MultiAgent", "Blackboard", "Message",
    "Indexer", "HybridRetriever", "Document", "chunk_markdown",
    "Graph", "Node", "once",
    "TrajectoryEvaluator", "EvalCase", "EvalResult",
    "Guardrail", "GuardedToolRegistry", "guard_agent", "Registry",
]
