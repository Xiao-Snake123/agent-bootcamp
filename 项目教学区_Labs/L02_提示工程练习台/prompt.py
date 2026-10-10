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


def truncate_to_tokens(text: str, max_tokens: int, approx_chars_per_token: float = 4.0) -> str:
    """极简截断：按"字数 / 每 token 字符数"估算，超过上限则截断并加省略号。

    真实场景应调用 tokenizer（如 tiktoken）精确计 token，这里用近似便于离线演示。
    """
    est = int(max_tokens * approx_chars_per_token)
    if len(text) <= est:
        return text
    return text[:est] + "…（已截断）"


def parse_json_block(text: str) -> dict:
    """从模型输出里抽取 JSON（兼容 ```json 围栏 与裸 JSON）。"""
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    return json.loads(candidate.strip())
