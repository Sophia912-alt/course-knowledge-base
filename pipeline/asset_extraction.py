"""
asset_extraction.py — 资产提取层

从 knowledge_base 中提取：
  - tools
  - websites
  - skills
要求：去重、统计频率、记录来源、按频率排序
"""

import os
from collections import Counter, defaultdict

from . import config
from .utils import write_json, read_json


def _accumulate_asset(knowledge: list[dict]) -> dict:
    """
    从 knowledge 列表中提取三类资产
    返回:
      { "tools": [{"name":..., "count":..., "sources":[...]}, ...],
        "websites": [...],
        "skills": [...] }
    """

    # name -> {"count": int, "sources": set}
    tools_acc = defaultdict(lambda: {"count": 0, "sources": set()})
    sites_acc = defaultdict(lambda: {"count": 0, "sources": set()})
    skills_acc = defaultdict(lambda: {"count": 0, "sources": set()})

    for item in knowledge:
        entities = item.get("entities", {})
        source = item.get("source", "unknown")

        for t in entities.get("tools", []):
            name = t.strip()
            if name:
                tools_acc[name]["count"] += 1
                tools_acc[name]["sources"].add(source)

        for w in entities.get("websites", []):
            name = w.strip()
            if name:
                sites_acc[name]["count"] += 1
                sites_acc[name]["sources"].add(source)

        for s in entities.get("skills", []):
            name = s.strip()
            if name:
                skills_acc[name]["count"] += 1
                skills_acc[name]["sources"].add(source)

    def to_sorted_list(acc) -> list[dict]:
        result = [
            {"name": name, "count": data["count"],
             "sources": sorted(data["sources"])}
            for name, data in acc.items()
        ]
        result.sort(key=lambda x: (-x["count"], x["name"]))
        return result

    return {
        "tools": to_sorted_list(tools_acc),
        "websites": to_sorted_list(sites_acc),
        "skills": to_sorted_list(skills_acc),
    }


def run_asset_extraction(knowledge: list[dict] = None) -> dict:
    """执行资产提取"""
    if knowledge is None:
        kb_path = os.path.join(config.KNOWLEDGE_BASE_DIR, "knowledge_base.json")
        if os.path.exists(kb_path):
            knowledge = read_json(kb_path)
        else:
            raise FileNotFoundError(f"未找到知识库: {kb_path}")

    print("\n" + "=" * 50)
    print("📦 [Step 5] Asset Extraction — 资产提取")
    print("=" * 50)

    assets = _accumulate_asset(knowledge)

    os.makedirs(config.ASSETS_DIR, exist_ok=True)

    # 分别保存
    for asset_type in ["tools", "websites", "skills"]:
        out_path = os.path.join(config.ASSETS_DIR, f"assets_{asset_type}.json")
        write_json(assets[asset_type], out_path)
        print(f"  ✓ {asset_type}: {len(assets[asset_type])} 项 -> {out_path}")

    # 全量
    all_path = os.path.join(config.ASSETS_DIR, "assets_all.json")
    write_json(assets, all_path)
    print(f"  ✓ 全量资产: {all_path}")

    # 打印 Top 10
    print("\n  📊 Top 10 Tools:")
    for t in assets["tools"][:10]:
        print(f"    {t['name']} (x{t['count']}) — {', '.join(t['sources'])}")

    print("\n  📊 Top 10 Skills:")
    for s in assets["skills"][:10]:
        print(f"    {s['name']} (x{s['count']}) — {', '.join(s['sources'])}")

    print("\n  📊 Top 10 Websites:")
    for w in assets["websites"][:10]:
        print(f"    {w['name']} (x{w['count']})")

    return assets
