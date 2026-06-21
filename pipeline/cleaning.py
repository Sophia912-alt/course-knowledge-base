"""
cleaning.py — 数据清洗层

将所有数据统一为：
  {"source": "", "type": "slides|transcript|feishu", "content": "", "timestamp": ""}
"""

import os
import re
from datetime import datetime

from . import config
from .utils import write_json, safe_filename


def _clean_text(text: str) -> str:
    """基础文本清洗：去除多余空行、控制字符"""
    # 去除图片 Markdown/HTML 引用
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'<img[^>]*>', '', text, flags=re.IGNORECASE)
    # 去除多余空行（保留单空行）
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 去除控制字符（保留换行/回车/制表）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text.strip()


def _detect_source_from_slides(filename: str) -> str:
    """从幻灯片文件名推断课程来源"""
    # 移除扩展名
    name = filename.replace(".md", "").strip()
    # 清理特殊字符
    name = name.replace("｜", " ").replace("|", " ").replace("_", " ")
    # 压缩多余空格
    name = " ".join(name.split())
    return name


def _detect_source_from_transcript(filename: str) -> str:
    """从转写文件名推断课程来源"""
    name = filename.replace(".txt", "").strip()
    name = " ".join(name.split())
    return name


def process_ingested_data(ingested: dict) -> list[dict]:
    """
    将原始导入数据清洗为标准格式并保存到 processed/
    返回清洗后的记录列表
    """
    print("\n" + "=" * 50)
    print("🧹 [Step 2] Cleaning — 数据清洗")
    print("=" * 50)

    records = []

    # ── Slides ──
    for item in ingested.get("slides", []):
        records.append({
            "source": _detect_source_from_slides(item["filename"]),
            "type": "slides",
            "content": _clean_text(item["content"]),
            "timestamp": datetime.now().isoformat(),
        })

    # ── Transcripts ──
    for item in ingested.get("transcripts", []):
        records.append({
            "source": _detect_source_from_transcript(item["filename"]),
            "type": "transcript",
            "content": _clean_text(item["content"]),
            "timestamp": datetime.now().isoformat(),
        })

    # ── Feishu ──
    for item in ingested.get("feishu", []):
        records.append({
            "source": "Feishu 群聊",
            "type": "feishu",
            "content": _clean_text(item.get("content", "")),
            "timestamp": item.get("create_time", datetime.now().isoformat()),
        })

    # 输出到 processed 文件夹
    os.makedirs(config.PROCESSED_DIR, exist_ok=True)

    # 按类型分组保存
    type_groups = {}
    for r in records:
        type_groups.setdefault(r["type"], []).append(r)

    for rec_type, recs in type_groups.items():
        out_path = os.path.join(config.PROCESSED_DIR, f"clean_{rec_type}.json")
        write_json(recs, out_path)

    # 也保存一份全量
    all_path = os.path.join(config.PROCESSED_DIR, "clean_all.json")
    write_json(records, all_path)

    print(f"  ✓ 清洗完成: {len(records)} 条记录")
    for t, recs in type_groups.items():
        print(f"    - {t}: {len(recs)} 条")
    print(f"    全量文件: {all_path}")

    return records
