"""
ingestion.py — 数据导入层

从 raw-slides / raw-transcripts 读取本地文件，
通过飞书 API 导入群聊消息到 raw-feishu。
"""

import os
import json
import time
from datetime import datetime

import requests

from . import config
from .utils import list_files, read_file_text, read_json, write_json


# ── 1. Slides ─────────────────────────────────────────────────

def ingest_slides() -> list[dict]:
    """读取 raw-slides 下所有 .md 文件"""
    files = list_files(config.RAW_SLIDES_DIR, "*.md")
    results = []
    for fp in files:
        content = read_file_text(fp)
        basename = os.path.basename(fp)
        results.append({
            "filename": basename,
            "raw_path": fp,
            "content": content,
        })
    print(f"  ✓ 课件导入: {len(results)} 个文件")
    return results


# ── 2. Transcripts ────────────────────────────────────────────

def ingest_transcripts() -> list[dict]:
    """读取 raw-transcripts 下所有 .txt 文件"""
    files = list_files(config.RAW_TRANSCRIPTS_DIR, "*.txt")
    results = []
    for fp in files:
        content = read_file_text(fp)
        basename = os.path.basename(fp)
        results.append({
            "filename": basename,
            "raw_path": fp,
            "content": content,
        })
    print(f"  ✓ 转写导入: {len(results)} 个文件")
    return results


# ── 3. Feishu（飞书）群聊 API ─────────────────────────────────

def _get_feishu_tenant_token(app_id: str, app_secret: str) -> str:
    """获取飞书 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(
        url,
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"飞书 token 获取失败: {data}")
    return data["tenant_access_token"]


def _fetch_feishu_messages(token: str, chat_id: str, page_size: int = 50,
                           max_pages: int = 20) -> list[dict]:
    """分页拉取群聊消息"""
    all_messages = []
    page_token = None
    for _ in range(max_pages):
        url = f"https://open.feishu.cn/open-apis/im/v1/messages"
        params = {
            "container_id_type": "chat",
            "container_id": chat_id,
            "page_size": page_size,
            "sort_type": "ByCreateTimeAsc",
        }
        if page_token:
            params["page_token"] = page_token

        resp = requests.get(
            url, headers={"Authorization": f"Bearer {token}"},
            params=params, timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"飞书消息获取失败: {data}")

        items = data.get("data", {}).get("items", [])
        all_messages.extend(items)

        if not data.get("data", {}).get("has_more"):
            break
        page_token = data["data"].get("page_token")

    return all_messages


def _ingest_feishu_manual_export() -> list[dict]:
    """读取 raw-feishu 中手动导出的群聊文件（支持 .txt / .csv）"""
    results = []
    txt_files = list_files(config.RAW_FEISHU_DIR, "*.txt")
    csv_files = list_files(config.RAW_FEISHU_DIR, "*.csv")

    all_files = txt_files + csv_files

    for fp in all_files:
        basename = os.path.basename(fp)
        # 跳过我们程序自己生成的控制文件
        if basename.startswith("_"):
            continue
        content = read_file_text(fp)
        lines = content.strip().split("\n")
        results.append({
            "filename": basename,
            "content": content,
            "lines": len(lines),
        })
        print(f"    ✓ 读取手动导出文件: {basename} ({len(lines)} 行)")

    return results


def ingest_feishu() -> list[dict]:
    """导入飞书群聊数据
    优先级:
      1. 手动导出的文件 (.txt / .csv 放在 raw-feishu/ 目录下)
      2. API 导入（需要凭据 + 机器人已在群中）
    """
    app_id = config.FEISHU_APP_ID
    app_secret = config.FEISHU_APP_SECRET
    chat_id = config.FEISHU_CHAT_ID

    # ── 优先检查手动导出文件 ──
    manual = _ingest_feishu_manual_export()
    if manual:
        print(f"  ✓ 飞书手动导入: {len(manual)} 个文件")
        return manual

    # ── 如果没有手动导出文件，尝试 API ──
    # 如果没配凭据，写入占位文件提示
    if not app_id or not app_secret:
        placeholder = {
            "status": "skipped",
            "message": "飞书 API 凭据未配置。请设置环境变量 FEISHU_APP_ID 和 FEISHU_APP_SECRET",
            "chat_id": chat_id,
            "note": "凭证获取方式 → 飞书开放平台 https://open.feishu.cn/ → 创建企业自建应用 → 获取 App ID / App Secret"
        }
        out_path = os.path.join(config.RAW_FEISHU_DIR, "_feishu_config_needed.json")
        write_json(placeholder, out_path)
        print(f"  ⚠ 飞书导入跳过: 请配置 FEISHU_APP_ID / FEISHU_APP_SECRET")
        print(f"    占位文件: {out_path}")
        return []

    print(f"  飞书 API 连接中...")
    try:
        token = _get_feishu_tenant_token(app_id, app_secret)
        messages = _fetch_feishu_messages(token, chat_id)
    except Exception as e:
        error_info = {
            "status": "error",
            "error": str(e),
            "chat_id": chat_id,
            "hint": "请确认: 1) 飞书应用已添加 'im:message' 权限 2) 机器人已加入该群聊 3) App ID/Secret 正确"
        }
        out_path = os.path.join(config.RAW_FEISHU_DIR, "_feishu_import_error.json")
        write_json(error_info, out_path)
        print(f"  ⚠ 飞书消息获取失败: {e}")
        print(f"    错误信息已保存至: {out_path}")
        return []

    # 清洗为简洁格式
    simplified = []
    for msg in messages:
        body = msg.get("body", {})
        content_raw = body.get("content", "{}")
        try:
            content_obj = json.loads(content_raw) if isinstance(content_raw, str) else {}
        except json.JSONDecodeError:
            content_obj = {"text": content_raw}

        simplified.append({
            "message_id": msg.get("message_id"),
            "sender": msg.get("sender", {}).get("id", ""),
            "msg_type": msg.get("msg_type", ""),
            "content": content_obj.get("text", content_raw),
            "create_time": msg.get("create_time", ""),
        })

    # 保存
    os.makedirs(config.RAW_FEISHU_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(config.RAW_FEISHU_DIR, f"feishu_messages_{timestamp}.json")
    write_json(simplified, out_path)

    print(f"  ✓ 飞书消息导入: {len(simplified)} 条")
    print(f"    保存至: {out_path}")
    return simplified


# ── 统一入口 ──────────────────────────────────────────────────

def run_ingestion() -> dict:
    """执行全部导入，返回 { type: [items] }"""
    print("\n" + "=" * 50)
    print("📥 [Step 1] Ingestion — 数据导入")
    print("=" * 50)

    slides = ingest_slides()
    transcripts = ingest_transcripts()
    feishu = ingest_feishu()

    return {
        "slides": slides,
        "transcripts": transcripts,
        "feishu": feishu,
    }
