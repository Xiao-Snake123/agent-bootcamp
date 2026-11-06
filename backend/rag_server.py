"""最小 RAG 问答原型（求职复习 Agent 助手）—— Qdrant 持久化优化版。

检索（.env 的 RETRIEVER 控制）：
  - bm25   : 纯 BM25，零依赖、免 key（默认）
  - vector : DashScope embedding + Qdrant 向量检索（需 DASHSCOPE_API_KEY）
  - hybrid : BM25 + 向量融合（推荐）
生成：DEEPSEEK_API_KEY；有则用 DeepSeek 生成（带引用），无则演示模式。
语料：content/核心机制篇/*.md
"""
import os
import re
import math
import glob
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

# 加载项目根目录 .env（rag_server 在 backend/，.env 在上两级）
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

app = FastAPI(title="Agent Bootcamp 求职复习问答助手(原型)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"
QDRANT_PATH = Path(__file__).resolve().parent / "qdrant_storage"
COLLECTION = "agent_bootcamp"

# ---- 配置 ----
EMBED_KEY = os.getenv("DASHSCOPE_API_KEY")
EMBED_MODEL = (os.getenv("DASHSCOPE_EMBED_MODEL") or "text-embedding-v3").strip()
EMBED_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
RETRIEVER = (os.getenv("RETRIEVER") or "bm25").strip().lower()

# ---- 语料加载 ----
def tokenize(text):
    return [t.lower() for t in re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]", text or "")]


def _mk(chapter, section, body, fp):
    return {"chapter": chapter, "section": section,
            "text": body.strip()[:1600], "src": Path(fp).name}


def load_chunks():
    chunks = []
    for fp in sorted(glob.glob(str(CONTENT_DIR / "**" / "*.md"), recursive=True)):
        text = Path(fp).read_text(encoding="utf-8")
        m = re.search(r"^#\s*(.+)$", text, re.M)
        chapter = m.group(1).strip() if m else Path(fp).stem
        parts = re.split(r"(?m)^##\s+(.+)$", text)
        chunks.append(_mk(chapter, "概览", parts[0], fp))
        for i in range(1, len(parts), 2):
            sec = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            chunks.append(_mk(chapter, sec, body, fp))
    return chunks


CHUNKS = load_chunks()
TOKENS = [tokenize(f"{c['chapter']} {c['section']} {c['text']}") for c in CHUNKS]
N = len(CHUNKS)
DF = {}
for toks in TOKENS:
    for w in set(toks):
        DF[w] = DF.get(w, 0) + 1
AVGDL = sum(len(t) for t in TOKENS) / max(N, 1)
K1, B = 1.5, 0.75


# ---- BM25 ----
def bm25(query, top_k=5):
    q = tokenize(query)
    scores = []
    for doc in TOKENS:
        score = 0.0
        dl = len(doc)
        freq = {}
        for w in doc:
            freq[w] = freq.get(w, 0) + 1
        for term in q:
            if term not in DF or DF[term] == 0:
                continue
            f = freq.get(term, 0)
            if f == 0:
                continue
            idf = math.log(1 + (N - DF[term] + 0.5) / (DF[term] + 0.5))
            score += idf * (f * (K1 + 1)) / (f + K1 * (1 - B + B * dl / AVGDL))
        scores.append(score)
    ranked = sorted(range(N), key=lambda i: scores[i], reverse=True)[:top_k]
    return [CHUNKS[i] for i in ranked if scores[i] > 0]


# ---- embedding（DashScope，分批）----
_embed_client_inst = None
_chunk_vecs = None
_qdrant = None
_qdrant_mode = None


def _embed_client():
    global _embed_client_inst
    if _embed_client_inst is None and EMBED_KEY:
        _embed_client_inst = OpenAI(api_key=EMBED_KEY, base_url=EMBED_BASE)
    return _embed_client_inst


def embed(texts):
    client = _embed_client()
    out = []
    batch = 8  # DashScope 单次 embedding 批量上限（<=10）
    for i in range(0, len(texts), batch):
        resp = client.embeddings.create(model=EMBED_MODEL, input=texts[i:i + batch])
        out.extend(d.embedding for d in resp.data)
    return out


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


# ---- Qdrant（本地持久化，失败降级内存）----
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    _QDRANT_OK = True
except ImportError:
    _QDRANT_OK = False


def _ensure_collection():
    dim = len(embed(["dim_probe"])[0])
    if not _qdrant.collection_exists(COLLECTION):
        _qdrant.create_collection(
            COLLECTION, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))
    cnt = _qdrant.count(COLLECTION).count
    if cnt != N:
        if cnt > 0:
            _qdrant.delete_collection(COLLECTION)
            _qdrant.create_collection(
                COLLECTION, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))
        vecs = embed([f"{c['chapter']} {c['section']} {c['text']}" for c in CHUNKS])
        _qdrant.upsert(COLLECTION, points=[
            PointStruct(id=i, vector=v,
                        payload={"chapter": c["chapter"], "section": c["section"],
                                 "text": c["text"], "src": c["src"]})
            for i, (c, v) in enumerate(zip(CHUNKS, vecs))
        ])


def _init_vectors():
    global _qdrant, _chunk_vecs, _qdrant_mode
    if not EMBED_KEY:
        print("[warn] 无 DASHSCOPE_API_KEY，向量检索不可用，仅 BM25")
        return
    if _QDRANT_OK:
        try:
            QDRANT_PATH.mkdir(exist_ok=True)
            _qdrant = QdrantClient(path=str(QDRANT_PATH))
            _ensure_collection()
            _qdrant_mode = "disk"
            print(f"[ok] Qdrant 本地持久化就绪（{_qdrant.count(COLLECTION).count} 向量）")
            return
        except Exception as e:
            print(f"[warn] Qdrant 本地模式失败，降级内存向量：{e}")
    _chunk_vecs = embed([f"{c['chapter']} {c['section']} {c['text']}" for c in CHUNKS])
    _qdrant_mode = "memory"
    print(f"[ok] 内存向量就绪（{len(_chunk_vecs)} 向量）")


def vector_search(q, top_k=5):
    qv = embed([q])[0]
    if _qdrant_mode == "disk" and _qdrant is not None:
        resp = _qdrant.query_points(COLLECTION, query=qv, limit=top_k)
        return [{"chapter": h.payload["chapter"], "section": h.payload["section"],
                 "text": h.payload["text"], "src": h.payload["src"]} for h in resp.points]
    scored = sorted(((cosine(qv, cv), i) for i, cv in enumerate(_chunk_vecs)),
                    reverse=True)
    return [CHUNKS[i] for s, i in scored[:top_k] if s > 0]


def hybrid_search(q, top_k=5):
    pool = vector_search(q, top_k) + bm25(q, top_k)
    seen, out = set(), []
    for c in pool:
        key = c["chapter"] + c["section"]
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out[:top_k]


if RETRIEVER in ("vector", "hybrid"):
    _init_vectors()
else:
    print(f"[info] RETRIEVER={RETRIEVER}，仅 BM25")


# ---- 生成（DeepSeek）----
def generate(question, ctx_chunks):
    key = os.getenv("DEEPSEEK_API_KEY")
    context = "\n\n".join(
        f"【{c['chapter']} / {c['section']}】\n{c['text']}" for c in ctx_chunks)
    if not key:
        demo = "\n\n".join(
            f"• {c['chapter']} / {c['section']}：{c['text'][:220]}…" for c in ctx_chunks)
        return ("【演示模式】未配置 DEEPSEEK_API_KEY，以下为检索到的相关片段；"
                "在 .env 填入 DeepSeek key 后即可生成综合回答：\n\n" + demo)
    client = OpenAI(api_key=key, base_url="https://api.deepseek.com/v1")
    prompt = (f"你是 Agent 开发求职复习助手。基于以下资料回答问题，"
              f"回答要面试向（含要点与常见坑），并标注引用章节。\n\n资料：\n{context}\n\n问题：{question}")
    resp = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        messages=[{"role": "system", "content": "严谨、紧扣资料、面试导向。"},
                  {"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def retrieve(q, top_k=5):
    if RETRIEVER == "vector":
        return vector_search(q, top_k)
    if RETRIEVER == "hybrid":
        return hybrid_search(q, top_k)
    return bm25(q, top_k)


@app.get("/ask")
def ask(q: str = Query(..., min_length=1)):
    chunks = retrieve(q, 5)
    answer = generate(q, chunks)
    return {"answer": answer,
            "sources": [{"chapter": c["chapter"], "section": c["section"]} for c in chunks],
            "retriever": RETRIEVER, "vector_mode": _qdrant_mode}


@app.get("/health")
def health():
    return {"status": "ok", "chunks": N, "retriever": RETRIEVER, "vector_mode": _qdrant_mode,
            "deepseek": bool(os.getenv("DEEPSEEK_API_KEY")),
            "dashscope_embed": bool(EMBED_KEY)}
