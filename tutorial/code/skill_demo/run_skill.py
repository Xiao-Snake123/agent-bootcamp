#!/usr/bin/env python3
"""演示 Agent 如何在运行时「按需加载并调用」一个 Skill。

真实项目里 Skill 由框架从 SKILL.md 元数据自动发现；这里用最小代码还原核心机制。
"""
import importlib
import os
import re

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))


def load_skill(name: str):
    """读取 SKILL.md 的 frontmatter，动态导入对应 handler。

    支持两种写法：单行标量（description: xxx）和多行列表（triggers:\\n  - a\\n  - b）。
    """
    meta_path = os.path.join(SKILL_DIR, "SKILL.md")
    text = open(meta_path, encoding="utf-8").read()
    fm = re.search(r"^---\n(.*?)\n---", text, re.S).group(1)
    meta, key, buf = {}, None, []
    for line in fm.splitlines():
        if line.startswith("  - "):           # 列表项
            buf.append(line[4:].strip())
        else:
            if key is not None:
                meta[key] = buf if buf else val
            if ":" in line:
                key, val = line.split(":", 1)
                key, val = key.strip(), val.strip()
                buf = []
                if val:                         # 单行标量
                    meta[key] = val
                    key = None
    if key is not None:
        meta[key] = buf if buf else val
    handler = importlib.import_module("handler")  # handler.py
    return meta, handler


def invoke(name: str, query: str) -> str:
    meta, handler = load_skill(name)
    return handler.search(query)


if __name__ == "__main__":
    print("触发词:", load_skill("doc-search")[0].get("triggers"))
    print("调用结果:", invoke("doc-search", "RAG"))
