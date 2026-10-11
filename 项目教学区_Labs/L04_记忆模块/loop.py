"""L04 演示：跨会话长期记忆 + 短期压缩（离线，无需 Key）。

运行：
    cd 项目教学区_Labs/L04_记忆模块
    python loop.py
"""

import os
import sys

# 让本脚本既能直接运行，也能被 pytest 导入：把 agent_core 与当前目录加入路径
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_core.llm import MockLLMClient
from agent_core.agent import Agent
from agent_core.tools import ToolRegistry
from agent_core.memory import LongTermMemory, BufferMemory
from memory_tools import SaveFactTool, RecallTool


class MemoryMock(MockLLMClient):
    """离线决策器：根据对话决定 save / recall / 终止。"""

    def complete(self, messages, **kwargs):
        user = next((m["content"] for m in messages if m.get("role") == "user"), "")
        tool_obs = [m["content"] for m in messages if m.get("role") == "tool"]

        if tool_obs:
            last = tool_obs[-1]
            if "已保存" in last:
                return '{"thought": "已写入长期记忆", "final_answer": "好的，我已记住你的信息"}'
            if last and "（未找到" not in last:
                return '{"thought": "从记忆取回", "final_answer": "你叫' + last + '"}'
            return '{"thought": "没查到", "final_answer": "我暂时想不起来"}'

        if "我叫" in user and "什么" not in user and "吗" not in user:
            name = user.replace("我叫", "").strip("。. ")
            return ('{"thought": "应存入长期记忆", "action": "SaveFact",'
                    ' "args": {"key": "user_name", "value": "' + name + '"}}')
        if "叫什么" in user or "名字" in user:
            return '{"thought": "应从长期记忆召回", "action": "Recall", "args": {"key": "user_name"}}'
        return '{"thought": "无需工具", "final_answer": "（Mock）已理解：' + user + '"}'


def demo_cross_session():
    print("=== 跨会话长期记忆 ===")
    mem = LongTermMemory(namespace="user_001")
    reg = ToolRegistry()
    reg.register(SaveFactTool(mem))
    reg.register(RecallTool(mem))
    agent = Agent(llm=MemoryMock(), tools=reg)

    print("【会话1】用户: 我叫小明")
    a1, _ = agent.run("我叫小明", max_steps=4)
    print("  最终:", a1)

    print("【会话2】用户: 我刚才说我叫什么？")
    a2, t2 = agent.run("我刚才说我叫什么？", max_steps=4)
    print("  最终:", a2)
    print("  → 会话2的上下文窗口里没有会话1的话，靠长期记忆检索注入才'记得'。")


def demo_compress():
    print("\n=== 短期记忆压缩（BufferMemory）===")
    buf = BufferMemory(window=20, keep=2)
    for i in range(8):
        buf.add(f"轮{i}的对话内容")
    print("压缩前条数:", len(buf.get(k=100)))
    buf.compress()
    print("压缩后条数:", len(buf.get(k=100)))
    print("压缩后内容:", buf.get(k=100))


if __name__ == "__main__":
    demo_cross_session()
    demo_compress()
