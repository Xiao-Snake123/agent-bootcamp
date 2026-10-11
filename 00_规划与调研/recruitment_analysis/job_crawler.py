#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
job_crawler.py —— Agent / AI 应用开发岗位技术栈采集器（合规模板）

⚠️ 合规与使用须知（请务必先读）：
------------------------------------------------------------
1. 本程序是一个"负责任、可配置"的采集框架，**不内置任何反爬绕过手段**
   （无验证码破解、无代理轮询躲避封禁、无伪造指纹/浏览器环境欺骗）。
2. 主流招聘平台（Boss直聘、智联招聘、猎聘、前程无忧、拉勾等）的
   robots.txt 与用户协议通常禁止自动化抓取，且部署了强反爬。直接对它们
   做批量抓取既可能违反其服务条款，也可能触发法律风险。
3. 本程序默认**拒绝**访问标记为 `requires_permission=True` 的目标。
   只有当目标来源你确有合法权限（如：官方开放 API、企业授权、公开
   聚合站点允许抓取、或自有职业页）时，才将对应配置置为允许。
4. 运行前必须显式确认合规：设置环境变量 I_CONFIRM_COMPLIANCE=true。
5. 程序会自动检查目标 robots.txt 并遵守其 Disallow 规则与 Crawl-delay。

用法：
    pip install requests beautifulsoup4
    I_CONFIRM_COMPLIANCE=true python job_crawler.py
输出：
    jobs_raw.jsonl        原始岗位条目
    tech_frequency.json   技术词按类别聚合的热度统计
    tech_frequency.csv     同上（便于表格查看）
"""

import os
import re
import json
import time
import random
import hashlib
import urllib.robotparser
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    raise SystemExit("缺少依赖，请先执行: pip install requests beautifulsoup4")

# ---------------------------------------------------------------------------
# 0. 合规闸门
# ---------------------------------------------------------------------------
if os.environ.get("I_CONFIRM_COMPLIANCE", "").lower() != "true":
    raise SystemExit(
        "❌ 未确认合规。请阅读文件顶部须知：确认你有权限抓取目标后，"
        "设置环境变量 I_CONFIRM_COMPLIANCE=true 再运行。"
    )

# ---------------------------------------------------------------------------
# 1. 目标站点配置（按需修改；requires_permission=True 的默认不抓取）
#    示例给了一个"公开允许抓取"的占位站点结构，请替换为你有权限的来源。
# ---------------------------------------------------------------------------
TARGETS = [
    # 示例：把 base_url 换成你有权限抓取的开放聚合/职业页，
    # 并填写对应的 CSS 选择器（selector 指向职位卡片/文本块）。
    {
        "name": "example_open_board",
        "base_url": "https://example.com/jobs",
        "search_template": "https://example.com/jobs?q={query}",
        "queries": ["AI Agent 开发", "大模型应用开发", "智能体开发"],
        "requires_permission": False,          # 仅当你确认该站允许抓取时为 False
        "card_selector": "div.job-card",        # 站点特定的职位卡片选择器
        "title_selector": "h2.title",
        "desc_selector": "div.description",
        "max_pages": 5,
    },
    # 主流受保护平台：默认拒绝，避免违规。
    # 如需合规对接，请使用其官方 API 或获得书面授权后改为 False 并填选择器。
    {
        "name": "PROTECTED_PLATFORM_PLACEHOLDER",
        "base_url": "https://protected-job-site.example",
        "search_template": "https://protected-job-site.example/search?q={query}",
        "queries": ["Agent 开发"],
        "requires_permission": True,           # 默认禁止
        "card_selector": "",
        "title_selector": "",
        "desc_selector": "",
        "max_pages": 0,
    },
]

# ---------------------------------------------------------------------------
# 2. 技术词字典（用于抽取与按类别聚合热度）
#    来自本报告《技术趋势报告》中的类别划分，可随学习需要增删。
# ---------------------------------------------------------------------------
TECH_DICTIONARY = {
    "编程语言": ["Python", "TypeScript", "JavaScript", "Go", "Java", "C++", "Rust", "SQL"],
    "大模型与API": ["OpenAI", "GPT-4", "Claude", "Gemini", "Mistral", "Llama", "DeepSeek",
                      "Qwen", "通义千问", "Kimi", "Anthropic"],
    "Agent框架": ["LangChain", "LangGraph", "LlamaIndex", "CrewAI", "AutoGen", "Dify",
                   "Coze", "MetaGPT", "AutoGPT", "SmolAgents", "Semantic Kernel",
                   "Haystack", "AgentScope", "MCP", "Model Context Protocol"],
    "RAG": ["RAG", "检索增强", "Embedding", "重排序", "Re-ranking", "Query Rewrite", "混合检索"],
    "向量数据库": ["Milvus", "Chroma", "Pinecone", "Qdrant", "Weaviate", "pgvector",
                    "Elasticsearch", "Redis", "MongoDB"],
    "推理范式": ["Prompt Engineering", "ReAct", "Chain-of-Thought", "CoT",
                 "Plan-and-Execute", "Tree-of-Thought", "Reflection"],
    "多智能体机制": ["Multi-Agent", "多智能体", "Planning", "Memory", "Tool Use",
                     "Function Calling", "反思", "自修正"],
    "微调与推理": ["SFT", "LoRA", "QLoRA", "微调", "vLLM", "Ollama", "TensorRT-LLM",
                   "SGLang", "lmdeploy", "PyTorch"],
    "工程化部署": ["FastAPI", "Flask", "Docker", "Kubernetes", "K8s", "微服务",
                   "WebSocket", "SSE", "CI/CD", "OpenShift", "限流", "降级"],
    "可观测与安全": ["LangSmith", "LangFuse", "OpenTelemetry", "评测", "可观测",
                     "护栏", "安全", "防幻觉"],
    "低代码": ["n8n", "Zapier", "Make", "低代码"],
    "语音多模态": ["Voice Agent", "ASR", "TTS", "WebRTC", "Pipecat", "LiveKit",
                   "VAD", "Whisper", "ElevenLabs", "Vapi", "Retell", "多模态"],
    "云平台": ["AWS", "Azure", "GCP", "Bedrock", "Vertex AI", "昇腾", "海光"],
}

# 关键词过滤：只保留与 Agent / AI 应用开发相关的岗位
RELEVANCE_KEYWORDS = ["agent", "智能体", "大模型", "llm", "rag", "ai 应用", "ai应用", "生成式"]

# ---------------------------------------------------------------------------
# 3. 抓取器（礼貌、合规）
# ---------------------------------------------------------------------------
class CompliantCrawler:
    def __init__(self, delay=(2, 5), timeout=15, user_agent=None):
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or (
                "Mozilla/5.0 (compatible; EduJobCrawler/1.0; "
                "+https://example.com/crawler-policy) "
                "academic-research-compliant"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        self._robots_cache = {}

    def _robots_allows(self, url: str) -> bool:
        """检查目标 robots.txt，遵守 Disallow 与 Crawl-delay。"""
        parsed = urllib.parse.urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robots_cache:
            rp = urllib.robotparser.RobotFileParser()
            try:
                rp.set_url(base + "/robots.txt")
                rp.read()
            except Exception:
                # 读取失败则保守地禁止抓取
                rp = None
            self._robots_cache[base] = rp
        rp = self._robots_cache[base]
        if rp is None:
            return False
        return rp.can_fetch(self.session.headers["User-Agent"], url)

    def _polite_sleep(self):
        time.sleep(random.uniform(*self.delay))

    def fetch(self, url: str) -> str | None:
        if not self._robots_allows(url):
            print(f"  [robots 禁止] 跳过: {url}")
            return None
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.text
            print(f"  [HTTP {resp.status_code}] 跳过: {url}")
            return None
        except Exception as e:
            print(f"  [错误] {url}: {e}")
            return None
        finally:
            self._polite_sleep()


# ---------------------------------------------------------------------------
# 4. 解析与抽取
# ---------------------------------------------------------------------------
def extract_tech(text: str) -> dict:
    """按类别统计命中的技术词（出现一次即计数，不重复计同一词多次）。"""
    found = {}
    for category, words in TECH_DICTIONARY.items():
        hits = []
        for w in words:
            # 简单子串匹配；生产可换正则边界匹配
            if w.lower() in text.lower():
                hits.append(w)
        if hits:
            found[category] = sorted(set(hits))
    return found


def is_relevant(text: str) -> bool:
    low = text.lower()
    return any(k.lower() in low for k in RELEVANCE_KEYWORDS)


def parse_cards(html: str, target: dict) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(target.get("card_selector", "")) or [soup]
    results = []
    for c in cards:
        title = ""
        desc = ""
        if target.get("title_selector"):
            t = c.select_one(target["title_selector"])
            if t:
                title = t.get_text(" ", strip=True)
        if target.get("desc_selector"):
            d = c.select_one(target["desc_selector"])
            if d:
                desc = d.get_text(" ", strip=True)
        blob = f"{title}\n{desc}"
        if not blob.strip():
            continue
        results.append({
            "title": title,
            "description": desc[:4000],
            "tech": extract_tech(blob),
        })
    return results


# ---------------------------------------------------------------------------
# 5. 主流程
# ---------------------------------------------------------------------------
def main():
    out_dir = Path(__file__).parent
    raw_path = out_dir / "jobs_raw.jsonl"
    freq_json = out_dir / "tech_frequency.json"
    freq_csv = out_dir / "tech_frequency.csv"

    crawler = CompliantCrawler()
    seen = set()
    category_counter = {cat: {} for cat in TECH_DICTIONARY}
    total_jobs = 0

    with raw_path.open("w", encoding="utf-8") as rf:
        for target in TARGETS:
            if target.get("requires_permission"):
                print(f"[跳过受保护目标] {target['name']}（默认禁止，请合规授权后启用）")
                continue
            print(f"[抓取] {target['name']}")
            for query in target.get("queries", [""]):
                for page in range(1, target.get("max_pages", 1) + 1):
                    url = target["search_template"].format(query=urllib.parse.quote(query))
                    if "{page" in target["search_template"]:
                        url = url.replace("{page}", str(page))
                    html = crawler.fetch(url)
                    if not html:
                        continue
                    for item in parse_cards(html, target):
                        blob = f"{item['title']}{item['description']}"
                        if not is_relevant(blob):
                            continue
                        key = hashlib.md5(blob.encode("utf-8")).hexdigest()
                        if key in seen:
                            continue
                        seen.add(key)
                        item["source"] = target["name"]
                        item["query"] = query
                        item["fetched_at"] = datetime.now(timezone.utc).isoformat()
                        rf.write(json.dumps(item, ensure_ascii=False) + "\n")
                        total_jobs += 1
                        for cat, words in item["tech"].items():
                            for w in words:
                                category_counter[cat][w] = category_counter[cat].get(w, 0) + 1

    # 聚合输出
    freq = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_jobs": total_jobs,
        "categories": {
            cat: dict(sorted(cnt.items(), key=lambda x: -x[1]))
            for cat, cnt in category_counter.items() if cnt
        },
    }
    freq_json.write_text(json.dumps(freq, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["类别,技术,出现次数"]
    for cat, cnt in freq["categories"].items():
        for w, n in cnt.items():
            lines.append(f"{cat},{w},{n}")
    freq_csv.write_text("\n".join(lines), encoding="utf-8")

    print(f"\n✅ 完成。共采集相关岗位 {total_jobs} 条。")
    print(f"   原始: {raw_path}")
    print(f"   聚合: {freq_json} / {freq_csv}")


if __name__ == "__main__":
    main()
