"""真实 API 连通性验证（填好 .env 后运行）。

    cd 项目教学区_Labs
    python 00_真实API接入/quickstart.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.config import build_llm

PROVIDER = "openai"  # 改成你用的：openai / deepseek / dashscope / zhipu / anthropic / custom


def main():
    llm = build_llm(PROVIDER)
    print(f"[provider={PROVIDER}] 客户端已构造：{type(llm).__name__}")
    out = llm.complete([{"role": "user", "content": "用一句话解释什么是 AI Agent。"}])
    print("模型回复：", out)


if __name__ == "__main__":
    main()
