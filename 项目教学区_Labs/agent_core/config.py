"""从 .env 加载配置，并提供 build_llm 工厂接入真实 API。

对应 design_docs：把"离线 Mock"与"真实后端"在 LLMClient 接口下统一切换。
所有 key 集中在项目根 .env（见 .env.example），不入库。

用法：
    from agent_core.config import build_llm
    llm = build_llm("openai")      # 读 .env 的 OPENAI_API_KEY
    llm = build_llm("deepseek")    # 读 DEEPSEEK_API_KEY + 预设 base_url
    llm = build_llm("anthropic")   # 读 ANTHROPIC_API_KEY
"""

import os
from dotenv import load_dotenv
from .llm import OpenAIClient, AnthropicClient

_HERE = os.path.dirname(os.path.abspath(__file__))   # agent_core
_ROOT = os.path.dirname(os.path.dirname(_HERE))        # 项目根（agent_core→Labs→根）


def load_env():
    """加载项目根 .env（幂等，重复调用无害）。"""
    load_dotenv(os.path.join(_ROOT, ".env"))


def get(key: str, default: str = ""):
    """读取环境变量（确保 .env 已加载）。"""
    load_env()
    return os.getenv(key, default)


def _require(env_name: str) -> str:
    """取出环境变量，缺失则抛清晰错误（提示去 .env 填写）。"""
    load_env()
    val = os.getenv(env_name)
    if not val:
        raise ValueError(
            f"缺少环境变量 {env_name}：请在项目根 .env 填写（参考 .env.example）"
        )
    return val


def build_llm(provider: str = "openai"):
    """按 provider 从 .env 构造真实 LLM 客户端（统一实现 complete()）。"""
    if provider == "openai":
        return OpenAIClient(api_key=_require("OPENAI_API_KEY"),
                             model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    if provider == "deepseek":
        return OpenAIClient(api_key=_require("DEEPSEEK_API_KEY"),
                             base_url="https://api.deepseek.com/v1",
                             model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
    if provider == "dashscope":
        return OpenAIClient(api_key=_require("DASHSCOPE_API_KEY"),
                             base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                             model=os.getenv("DASHSCOPE_MODEL", "qwen-plus"))
    if provider == "zhipu":
        return OpenAIClient(api_key=_require("ZHIPU_API_KEY"),
                             base_url="https://open.bigmodel.cn/api/paas/v4",
                             model=os.getenv("ZHIPU_MODEL", "glm-4"))
    if provider == "custom":
        return OpenAIClient(api_key=_require("CUSTOM_API_KEY"),
                             base_url=_require("CUSTOM_BASE_URL"),
                             model=_require("CUSTOM_MODEL"))
    if provider == "anthropic":
        return AnthropicClient(api_key=_require("ANTHROPIC_API_KEY"),
                               model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"))
    raise ValueError(
        f"未知 provider: {provider}（可选 openai/deepseek/dashscope/zhipu/custom/anthropic）"
    )
