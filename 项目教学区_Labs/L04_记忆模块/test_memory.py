"""L04 验收：长期记忆 save/recall + 短期压缩 + 跨会话 Agent 能召回。"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_core.memory import LongTermMemory, BufferMemory
from agent_core.llm import MockLLMClient
from agent_core.agent import Agent
from agent_core.tools import ToolRegistry
from memory_tools import SaveFactTool, RecallTool


def test_longterm_save_recall():
    m = LongTermMemory()
    m.save_fact("user_name", "小明")
    assert m.recall("user_name") == "小明"
    assert m.recall("user") == "小明"      # 子串回退，近似语义召回


def test_buffer_compress_reduces_count():
    buf = BufferMemory(window=20, keep=2)
    for i in range(8):
        buf.add(f"turn{i}")
    assert len(buf.get(k=100)) == 8
    buf.compress()
    assert len(buf.get(k=100)) == 1
    assert "摘要" in buf.get(k=100)[0]


def test_cross_session_agent_recalls():
    class MemoryMock(MockLLMClient):
        def complete(self, messages, **kwargs):
            user = next((m["content"] for m in messages if m.get("role") == "user"), "")
            obs = [m["content"] for m in messages if m.get("role") == "tool"]
            if obs:
                last = obs[-1]
                if "已保存" in last:
                    return '{"final_answer": "已记住"}'
                if last and "（未找到" not in last:
                    return '{"final_answer": "你叫' + last + '"}'
                return '{"final_answer": "想不起"}'
            if "我叫" in user and "什么" not in user:
                name = user.replace("我叫", "").strip()
                return '{"action": "SaveFact", "args": {"key": "user_name", "value": "' + name + '"}}'
            if "叫什么" in user:
                return '{"action": "Recall", "args": {"key": "user_name"}}'
            return '{"final_answer": "ok"}'

    mem = LongTermMemory()
    reg = ToolRegistry()
    reg.register(SaveFactTool(mem))
    reg.register(RecallTool(mem))
    agent = Agent(llm=MemoryMock(), tools=reg)
    agent.run("我叫小红", max_steps=4)
    _, traj = agent.run("我叫什么？", max_steps=4)
    assert traj.final_answer == "你叫小红"
