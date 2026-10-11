"""L08 生成：把检索到的 chunk 拼接进上下文，离线模板产出带出处的答案。

真实 RAG 这里应把 chunks 拼进 prompt 交给 LLM 做 grounded generation。
本 Lab 用模板演示"检索注入 + 出处标注"——出处（chunk id + source）是
K8 强调的可审计证据链，缺失则幻觉难查（陷阱③）。
"""


class Generator:
    def generate(self, question: str, chunks):
        if not chunks:
            return "（未检索到相关文档，无法回答）"
        cites = ", ".join(f"[{c['id']}:{c['source']}]" for c in chunks)
        ctx = "；".join(c["text"] for c in chunks)
        return f"问题：{question}\n根据 {cites}：{ctx}"
