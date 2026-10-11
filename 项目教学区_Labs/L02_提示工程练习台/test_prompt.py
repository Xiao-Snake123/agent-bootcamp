"""L02 pytest 验收测试。运行：pytest test_prompt.py"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import prompt
import challenge


def test_system_prompt_injected():
    """验收：system 提示应作为 messages 首条。"""
    msgs = prompt.PromptBuilder().with_system("你是助手").with_query("hi").as_messages()
    assert msgs[0] == {"role": "system", "content": "你是助手"}
    assert msgs[-1] == {"role": "user", "content": "hi"}


def test_few_shot_order():
    """验收：few-shot 应保持 user/assistant 交替，且在 query 之前。"""
    msgs = (prompt.PromptBuilder()
            .with_few_shot([("q1", "a1"), ("q2", "a2")])
            .with_query("q3").as_messages())
    roles = [m["role"] for m in msgs]
    assert roles == ["user", "assistant", "user", "assistant", "user"]


def test_structured_output_appends_schema():
    """验收：结构化输出约束应写进 system，且含 schema 关键字段。"""
    schema = {"properties": {"label": "string"}}
    msgs = (prompt.PromptBuilder().with_system("你是分类器")
            .with_structured_output(schema)
            .with_query("x").as_messages())
    assert "只输出一个 JSON" in msgs[0]["content"]
    assert "label" in msgs[0]["content"]


def test_truncate_caps_length():
    """验收：超长文本被截断并标记。"""
    text = "字" * 1000
    out = prompt.truncate_to_tokens(text, 10)
    assert out.endswith("（已截断）")
    assert len(out) < len(text)


def test_parse_json_block_handles_fence():
    """验收：能从 ```json 围栏 与裸 JSON 两种形态抽到 dict。"""
    fenced = '```json\n{"label": "正面"}\n```'
    assert prompt.parse_json_block(fenced) == {"label": "正面"}
    assert prompt.parse_json_block('{"label":"负面"}') == {"label": "负面"}


def test_challenge_bad_prompt_wanders():
    """验收：糟糕提示（无格式约束）下模型不吐结构化字段。"""
    out = challenge.ChallengeLLM().complete(
        [{"role": "system", "content": challenge.BAD_SYSTEM},
         {"role": "user", "content": "我要取消三杯咖啡"}])
    assert "intent" not in out


def test_challenge_good_prompt_yields_json():
    """验收：按 K02 方法写的好提示下模型吐合规 JSON。"""
    out = challenge.ChallengeLLM().complete(
        [{"role": "system", "content": challenge.REFERENCE_GOOD},
         {"role": "user", "content": "来3个披萨"}])
    assert '"intent"' in out and "披萨" in out


def test_cache_savings_is_positive():
    """验收：prompt caching 在多轮下确实节省 token（离线估算）。"""
    sav = prompt.estimate_cache_savings("长 system 约束", n_rounds=5, query_text="q")
    assert sav["with_cache_total"] < sav["no_cache_total"]
    assert sav["saved_tokens"] > 0
    assert sav["saved_pct"] > 0
