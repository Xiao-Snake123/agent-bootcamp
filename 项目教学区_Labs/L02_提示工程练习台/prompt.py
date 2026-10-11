"""L02 提示工程工具：可复用的 PromptBuilder（对应 K02）。

设计要点：
- 把"系统提示 / Few-shot 示例 / 用户查询 / 结构化输出约束"封装成可组合的积木，
  产出符合 OpenAI Chat 协议格式的 messages，后续 K3–K11 的 Lab 都复用它。
- 同时提供 truncate_to_tokens 帮助理解"上下文窗口"硬上限，以及
  parse_json_block 帮助从模型输出里稳定抽取 JSON（结构化输出配套）。
- 本文件零依赖、可离线跑，不 import agent_core，方便单测。

前沿注记：真实项目里 system + few-shot 这类稳定前缀应走 **prompt caching**
（Anthropic/OpenAI）降本提速；结构化输出优先用模型原生 structured outputs /
function calling（见 K02 第六节），本 Builder 仅做协议层组装，提示"内容"由你按
K02 第四节方法写。
"""

import json
import re


class PromptBuilder:
    """逐步组装发给 LLM 的 messages。

    典型用法：
        msgs = (PromptBuilder()
                .with_system("你是情感分类器")
                .with_few_shot([("物流快", "正面"), ("包装破", "负面")])
                .with_structured_output({"properties": {"label": "string"}})
                .with_query("客服态度好")
                .as_messages())
    """

    def __init__(self):
        self._system = ""
        self._shots = []   # list of {"role": "user"/"assistant", "content": ...}
        self._query = ""

    def with_system(self, prompt: str) -> "PromptBuilder":
        self._system = prompt
        return self

    def with_few_shot(self, examples: list) -> "PromptBuilder":
        """examples: [(user_text, assistant_text), ...]"""
        for u, a in examples:
            self._shots.append({"role": "user", "content": u})
            self._shots.append({"role": "assistant", "content": a})
        return self

    def with_query(self, text: str) -> "PromptBuilder":
        self._query = text
        return self

    def with_structured_output(self, schema: dict) -> "PromptBuilder":
        """追加一条约束：要求模型只输出符合 schema 的 JSON。"""
        instr = (
            "只输出一个 JSON 对象，且字段严格匹配以下 schema，不要任何额外说明：\n"
            + json.dumps(schema, ensure_ascii=False)
        )
        self._system = (self._system + "\n" + instr) if self._system else instr
        return self

    def as_messages(self) -> list:
        msgs = []
        if self._system:
            msgs.append({"role": "system", "content": self._system})
        msgs.extend(self._shots)
        if self._query:
            msgs.append({"role": "user", "content": self._query})
        return msgs


try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")
    def _count_tokens(text: str) -> int:
        return len(_ENC.encode(text))
except Exception:
    _ENC = None
    def _count_tokens(text: str) -> int:
        # 离线兜底：中文约 1–2 字/token，英文约 4 字符/token，取近似
        return max(1, int(len(text) / 4))


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """按 token 上限截断（优先 tiktoken 精确计数，不可用时退化为字数近似）。

    真实场景必须按 token 截断而非字符：中文一个字常占 1–2 token，
    纯字数近似会让长中文文本悄悄超出上下文窗口（呼应 K2 lost-in-the-middle）。
    """
    if _count_tokens(text) <= max_tokens:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if _count_tokens(text[:mid]) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + "…（已截断）"


def estimate_cache_savings(system_prompt: str, n_rounds: int, query_text: str = "") -> dict:
    """离线估算 prompt caching 的收益（不依赖真实 API）。

    机制：Agent 每轮都把同一段稳定 system 重发给模型。开启 caching 后，
    仅第一次计 system 的写入成本，后续轮次命中缓存（cache_read）只计 query。
    这里用 token 计数演示"省了多少"。
    """
    sys_tok = _count_tokens(system_prompt)
    q_tok = _count_tokens(query_text)
    no_cache = n_rounds * (sys_tok + q_tok)
    with_cache = sys_tok + n_rounds * q_tok
    saved = no_cache - with_cache
    return {
        "system_tokens": sys_tok,
        "per_round_tokens": sys_tok + q_tok,
        "no_cache_total": no_cache,
        "with_cache_total": with_cache,
        "saved_tokens": saved,
        "saved_pct": round(100 * saved / no_cache, 1) if no_cache else 0.0,
    }


def parse_json_block(text: str) -> dict:
    """从模型输出里抽取 JSON（兼容 ```json 围栏 与裸 JSON）。"""
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    return json.loads(candidate.strip())
