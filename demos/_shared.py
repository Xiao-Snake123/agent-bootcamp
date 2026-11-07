"""12 章可运行 demo 的统一运行约定。

- 默认：有 DEEPSEEK_API_KEY 就接真实 DeepSeek（deepseek-chat）；
- ``--offline`` 或无 key：自动降级为可脚本化的 MockLLMClient（零成本、可 CI）；
- 预算护栏：AGENT_MAX_COST（默认 0.30 元）/ ``--max-cost``，超限由 CostLimitError 截断；
- 所有 demo 共用 max_steps 上限，绝不无限循环。

运行：``python demos/demo_01_react.py --offline`` 或 ``python demos/demo_01_react.py``
"""
from __future__ import annotations

import argparse
import ast
import operator
import sys
from pathlib import Path

_DEMOS = Path(__file__).resolve().parent
ROOT = _DEMOS.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core import (
    Agent, CostLimitError, MockLLMClient, Trajectory, Step, Observation,
    build_llm, default_budget, get, make_tool, ToolRegistry, tool_call,
    BufferMemory, SummaryMemory, LongTermMemory,
    Planner, Plan, PlanStep, Reflector, Reflection,
    MultiAgent, Blackboard, Message,
    Indexer, HybridRetriever, Document, chunk_markdown,
    Graph, Node, once,
    TrajectoryEvaluator, EvalCase, EvalResult,
    Guardrail, GuardedToolRegistry, guard_agent,
)

CONTENT_DIR = ROOT / "content" / "核心机制篇"
TUTORIAL_DIR = ROOT / "tutorial" / "code"


def cli(chapter: int, title: str):
    parser = argparse.ArgumentParser(description=f"第 {chapter} 章 demo：{title}")
    parser.add_argument("--offline", action="store_true", help="强制离线 Mock，不调用真实 API")
    parser.add_argument("--max-cost", type=float, default=None, help="本次预算上限（元）")
    parser.add_argument("--goal", default=None, help="覆盖默认提问目标")
    parser.add_argument("--vector", action="store_true",
                        help="第7章：额外启用 DashScope embedding 做 hybrid 向量检索（会产生调用费用）")
    return parser.parse_args()


def make_llm(args, script=None):
    budget = args.max_cost if args.max_cost is not None else default_budget()
    if args.offline or not get("DEEPSEEK_API_KEY"):
        return MockLLMClient(script=script, max_cost=budget)
    return build_llm("deepseek", max_cost=budget)


def show_header(chapter: int, title: str, llm, args):
    mode = "离线 Mock" if llm.model == "mock" else f"真实 {llm.model}"
    print(f"\n=== 第 {chapter} 章 · {title} ===")
    print(f"模式: {mode} | 预算上限: {llm.max_cost} 元 | "
          f"关联网页模块: /modules/{chapter:02d}")


def show_trajectory(traj: Trajectory):
    print(f"终止原因: {traj.stop_reason} | 步数: {len(traj.steps)} | "
          f"失败工具调用: {len(traj.failed_calls)}")
    for i, step in enumerate(traj.steps, 1):
        name = step.action.get("name", "-")
        print(f"  {i}. {name}{step.action.get('args', {})} "
              f"-> {step.observation[:90]} [ok={step.ok}]")


def show_usage(llm):
    u = llm.usage
    print(f"用量: calls={u.calls} tokens={u.total_tokens} "
          f"cost≈{u.cost:.6f} 元（护栏估算，非账单）")


def approx_tokens(text: str) -> int:
    """中文约 1.5 字符/token 的粗估，仅用于教学演示上下文预算。"""
    return max(1, len(text) * 2 // 3)


def safe_calc(expr: str) -> str:
    """受限四则运算求值：不 eval 任意代码（第 11 章最小权限的正面示例）。"""
    ops = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv,
           ast.Pow: operator.pow}

    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return +ev(node.operand) if isinstance(node.op, ast.UAdd) else -ev(node.operand)
        raise ValueError("仅支持四则运算")

    return str(ev(ast.parse(expr, mode="eval").body))


def run(chapter: int, title: str, fn, script=None):
    """统一入口：解析参数 → 造 LLM → 执行 demo → 打印用量 → 处理护栏异常。"""
    args = cli(chapter, title)
    llm = make_llm(args, script)
    show_header(chapter, title, llm, args)
    try:
        fn(llm, args)
    except CostLimitError as e:
        print(f"[成本护栏触发，已安全停止] {e}")
    finally:
        show_usage(llm)
    return llm
