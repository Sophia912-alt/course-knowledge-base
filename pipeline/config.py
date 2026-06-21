"""
Pipeline 配置 — 所有路径、API 密钥、参数集中管理
"""

import os

# ── 项目根目录 ──────────────────────────────────────────────
BASE_DIR = "/Users/sophia/Desktop/AI学习库"

# ── 数据路径 ──────────────────────────────────────────────────
RAW_SLIDES_DIR      = os.path.join(BASE_DIR, "raw-slides")
RAW_TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "raw-transcripts")
RAW_FEISHU_DIR      = os.path.join(BASE_DIR, "raw-feishu")
PROCESSED_DIR       = os.path.join(BASE_DIR, "processed")
KNOWLEDGE_BASE_DIR  = os.path.join(BASE_DIR, "knowledge_base")
COURSE_SUMMARIES_DIR = os.path.join(BASE_DIR, "course_summaries")
ASSETS_DIR          = os.path.join(BASE_DIR, "assets")

# ── 目录映射（用于 mkdir） ──────────────────────────────────
ALL_DIRS = [
    RAW_SLIDES_DIR, RAW_TRANSCRIPTS_DIR, RAW_FEISHU_DIR,
    PROCESSED_DIR, KNOWLEDGE_BASE_DIR, COURSE_SUMMARIES_DIR, ASSETS_DIR,
]

# ── 安全读取环境变量 ────────────────────────────────────────
def _get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)

# ── LLM 配置（OpenAI 兼容 API） ──────────────────────────────
# 通过环境变量设置（推荐）
#   export OPENAI_BASE_URL="https://api.deepseek.com"
#   export OPENAI_API_KEY="sk-..."
OPENAI_BASE_URL = _get_env("OPENAI_BASE_URL", "https://api.deepseek.com")
OPENAI_API_KEY  = _get_env("OPENAI_API_KEY", "")
OPENAI_MODEL    = _get_env("PIPELINE_MODEL", "deepseek-chat")
LLM_MAX_RETRIES = 3
LLM_TIMEOUT     = 60

# ── 飞书 API 配置 ────────────────────────────────────────────
FEISHU_APP_ID     = _get_env("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = _get_env("FEISHU_APP_SECRET", "")
FEISHU_CHAT_ID    = "oc_c13eafb37a74370bf387edf886f9ae6c"
