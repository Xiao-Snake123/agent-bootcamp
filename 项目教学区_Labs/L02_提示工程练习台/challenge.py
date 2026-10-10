"""L02 技能演练：把一条糟糕提示改好，跑起来看模型行为差异。

配合 K02 第四节「怎么写一条好提示」。这里把"口语→订餐 JSON"任务变成可运行演练：
- BAD_SYSTEM：典型糟糕提示（指令模糊、无格式约束、无示例）；
- REFERENCE_GOOD：按 K02 方法写出的参考好提示；
- YOUR_SYSTEM：留空给你填，写完运行 `python main.py` 对比 BAD / REFERENCE / YOUR。

用 ChallengeLLM（离线）演示：糟糕提示下模型自由发挥、好提示下吐合规 JSON。
"""

import json
import re
from agent_core.llm import LLMClient


BAD_SYSTEM = "你帮用户处理订单。"

REFERENCE_GOOD = """你是订餐意图解析助手。
任务：把用户口语转成 JSON。字段 intent（枚举 order/cancel/query）、items（数组，每项 name 字符串 + qty 整数）。
约束：只输出 JSON，不要任何解释或多余文字。
示例：
用户：来两个汉堡
{"intent":"order","items":[{"name":"汉堡","qty":2}]}
"""

# ↓↓↓ 学员按 K02 方法写一条好提示，替换下面占位 ↓↓↓
YOUR_SYSTEM = ""


class ChallengeLLM(LLMClient):
    """离线演示：系统提示含格式约束时返回结构化 JSON，否则自由发挥。"""

    def complete(self, messages, **kwargs):
        sys_ = next((m["content"] for m in messages if m.get("role") == "system"), "")
        usr = next((m["content"] for m in messages if m.get("role") == "user"), "")
        if "只输出 JSON" in sys_ or "只输出一个 JSON" in sys_:
            if "取消" in usr:
                return json.dumps({"intent": "cancel", "items": []}, ensure_ascii=False)
            m = re.search(r"(\d+)\s*个\s*(\w+)", usr)
            if m:
                return json.dumps({"intent": "order",
                                   "items": [{"name": m.group(2), "qty": int(m.group(1))}]},
                                  ensure_ascii=False)
            return json.dumps({"intent": "order", "items": []}, ensure_ascii=False)
        return "好的，我已经记下您的请求。"


def run_challenge():
    llm = ChallengeLLM()
    task = "我要取消昨天点的三杯咖啡"
    print(f"\n=== ⑥ 技能演练（任务：{task}）===")
    bad = llm.complete([{"role": "system", "content": BAD_SYSTEM},
                        {"role": "user", "content": task}])
    good = llm.complete([{"role": "system", "content": REFERENCE_GOOD},
                         {"role": "user", "content": task}])
    print(f"  [BAD 提示]       → {bad}")
    print(f"  [参考好提示]     → {good}")
    if YOUR_SYSTEM.strip():
        yours = llm.complete([{"role": "system", "content": YOUR_SYSTEM},
                              {"role": "user", "content": task}])
        print(f"  [你的提示]       → {yours}")
    else:
        print("  [你的提示]       尚未填写 challenge.py 的 YOUR_SYSTEM（按 K02 方法写一条好提示再运行）")
