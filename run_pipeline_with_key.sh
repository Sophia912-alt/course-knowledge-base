#!/bin/bash
# ============================================================
# Course Knowledge Base Pipeline — 课程知识库自动构建工具
# ============================================================
# 用法:
#   1. 填入你的 API Key
#   2. 双击运行，或终端执行: bash run_pipeline_with_key.sh
# ============================================================

# ── 在这里填入你的 API Key ──
# 支持的 API: OpenAI / DeepSeek / 任何 OpenAI 兼容接口
# 去 https://platform.openai.com/api-keys 或 https://platform.deepseek.com 获取
export OPENAI_API_KEY="YOUR_API_KEY_HERE"
export OPENAI_BASE_URL="https://api.deepseek.com"   # 或其他兼容地址
export PIPELINE_MODEL="deepseek-chat"                # 模型名称

# ── 运行 ──
cd "$(dirname "$0")"
python3 run_pipeline.py "$@" && python3 -m pipeline.export_markdown
