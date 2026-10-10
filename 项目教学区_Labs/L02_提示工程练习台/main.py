"""L02 演示：提示工程如何改变模型行为（离线、无需 Key）。

构造四类 prompt 并喂给一个"真的读取 system 提示"的演示用 LLM，直观看到：
  1) 有无系统提示 → 输出形态不同；
  2) Few-shot 示例 → 模型模仿示例格式；
  3) 结构化输出约束 → 模型只吐 JSON；
  4) 上下文窗口 → 超长文本必须截断。
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import json
from agent_core.llm import LLMClient
from prompt import PromptBuilder, truncate_to_tokens, parse_json_block


class DemoLLM(LLMClient):
    """演示用决策器：真的读取 system 提示来决定输出形态（离线、无网络）。"""

    def complete(self, messages, **kwargs):
        system = next((m["content"] for m in messages if m.get("role") == "system"), "")
        user = next((m["content"] for m in messages if m.get("role") == "user"), "")

        if "只输出一个 JSON" in system:
            return json.dumps({"label": "正面", "score": 0.92}, ensure_ascii=False)
        # 模仿 few-shot 的最后一条 assistant 格式（正面/负面）
        shots = [m["content"] for m in messages if m.get("role") == "assistant"]
        if shots and shots[-1] in ("正面", "负面"):
            return "正面" if any(w in user for w in ("好", "快", "棒")) else "负面"
        if "用一句话" in system:
            return "这是一条正面评论。"
        return f"（模型）针对「{user}」的回复。"


def _show(title, messages):
    print(f"\n=== {title} ===")
    for m in messages:
        print(f"  [{m['role']}] {m['content']}")
    return messages


def main():
    llm = DemoLLM()

    # 1) 无系统提示
    m1 = PromptBuilder().with_query("这家店服务真差。").as_messages()
    _show("① 无系统提示", m1)
    print("  →", llm.complete(m1))

    # 2) 加系统提示（语气约束）
    m2 = (PromptBuilder()
          .with_system("你是一个简洁的评论分析助手，用一句话总结情感。")
          .with_query("这家店服务真差。")
          .as_messages())
    _show("② 加系统提示", m2)
    print("  →", llm.complete(m2))

    # 3) Few-shot 示例
    m3 = (PromptBuilder()
          .with_system("你是情感分类器，模仿示例输出。")
          .with_few_shot([("物流很快", "正面"), ("包装破损", "负面")])
          .with_query("客服态度好")
          .as_messages())
    _show("③ Few-shot", m3)
    print("  →", llm.complete(m3))

    # 4) 结构化输出
    schema = {"type": "object", "properties": {"label": "string", "score": "number"}}
    m4 = (PromptBuilder()
          .with_system("你是情感分类器。")
          .with_structured_output(schema)
          .with_query("这家店服务真差。")
          .as_messages())
    _show("④ 结构化输出", m4)
    out = llm.complete(m4)
    print("  →", out)
    print("  parse_json_block →", parse_json_block(out))

    # 5) 上下文窗口截断演示
    long_text = "字" * 1000
    print("\n=== ⑤ 上下文截断 ===")
    print("  原文长度", len(long_text),
          "→ 截到 50 token:", truncate_to_tokens(long_text, 50))


if __name__ == "__main__":
    main()
