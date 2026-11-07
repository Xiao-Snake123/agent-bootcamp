"""包内共享小工具：健壮 JSON 提取、中英混排分词。"""
from __future__ import annotations

import json
import re


def extract_json(text: str):
    """从 LLM 输出里抠出 JSON（容忍 ```json 围栏与前后解释文字）。"""
    if not isinstance(text, str):
        return None
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip())
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass
    match = re.search(r"[\[{].*[\]}]", cleaned, re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except (json.JSONDecodeError, ValueError):
            return None
    return None


def tokenize(text: str) -> list:
    """中文按单字、英文数字按词，够 BM25 / 关键词匹配用。"""
    return [t.lower() for t in re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]", text or "")]
