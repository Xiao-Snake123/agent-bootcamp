"""配置层（v2）：.env 统一从项目根读，build_llm 默认 DeepSeek 真跑。

保留 v1 的 load_env / get / _require / build_llm(provider) 接口，
新增：统一预算 AGENT_MAX_COST、单价 LLM_PRICE_IN/OUT、auto_llm 离线降级。
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from .llm import LLMClient, MockLLMClient, OpenAICompatibleClient

_ROOT = Path(__file__).resolve().parent.parent  # agent_core/ -> 项目根
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

_PROVIDERS = {
    "deepseek": ("DEEPSEEK_API_KEY", "DEEPSEEK_MODEL", "deepseek-chat", DEEPSEEK_BASE_URL),
    "dashscope": ("DASHSCOPE_API_KEY", "DASHSCOPE_MODEL", "qwen-plus", DASHSCOPE_BASE_URL),
    "openai": ("OPENAI_API_KEY", "OPENAI_MODEL", "gpt-4o-mini", ""),
    "zhipu": ("ZHIPU_API_KEY", "ZHIPU_MODEL", "glm-4", "https://open.bigmodel.cn/api/paas/v4"),
}


def load_env():
    """加载项目根 .env（幂等）。"""
    load_dotenv(_ROOT / ".env")


def get(key: str, default: str = "") -> str:
    load_env()
    return os.getenv(key, default)


def _require(env_name: str) -> str:
    value = get(env_name)
    if not value:
        raise ValueError(
            f"缺少环境变量 {env_name}：请在项目根 .env 填写（参考 .env.example），"
            f"或使用 offline=True 走离线 Mock")
    return value


def default_budget() -> float:
    """demo 默认预算（元），防止接真实 API 后无限循环烧钱。"""
    try:
        return float(get("AGENT_MAX_COST", "0.30"))
    except ValueError:
        return 0.30


def _prices() -> tuple:
    try:
        return float(get("LLM_PRICE_IN", "2.0")), float(get("LLM_PRICE_OUT", "8.0"))
    except ValueError:
        return 2.0, 8.0


def build_llm(provider: str = "deepseek", max_cost: float | None = None,
              offline: bool = False, **kwargs) -> LLMClient:
    """按 provider 构造 LLM 客户端；offline=True 直接返回可脚本化的 Mock。"""
    budget = default_budget() if max_cost is None else max_cost
    if offline:
        return MockLLMClient(max_cost=budget, **kwargs)

    price_in, price_out = _prices()
    common = dict(max_cost=budget, price_in=price_in, price_out=price_out)

    if provider == "custom":
        return OpenAICompatibleClient(
            api_key=_require("CUSTOM_API_KEY"), base_url=_require("CUSTOM_BASE_URL"),
            model=_require("CUSTOM_MODEL"), **common)
    if provider not in _PROVIDERS:
        raise ValueError(f"未知 provider: {provider}（可选 {', '.join(_PROVIDERS)} / custom）")

    key_env, model_env, fallback_model, base_url = _PROVIDERS[provider]
    return OpenAICompatibleClient(
        api_key=_require(key_env), base_url=base_url,
        model=get(model_env, fallback_model), **common)


def auto_llm(provider: str = "deepseek", max_cost: float | None = None,
             **kwargs) -> LLMClient:
    """有 key 走真实 API，缺 key 自动降级 Mock（demo 默认入口）。"""
    key_env = _PROVIDERS.get(provider, ("", "", "", ""))[0]
    if key_env and not get(key_env):
        return MockLLMClient(max_cost=default_budget() if max_cost is None else max_cost,
                             **kwargs)
    return build_llm(provider, max_cost=max_cost, **kwargs)
