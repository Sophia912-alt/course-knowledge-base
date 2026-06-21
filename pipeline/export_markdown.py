"""
export_markdown.py — 将 JSON 知识库导出为 Obsidian 兼容的 Markdown 文件

用法:
  python3 -m pipeline.export_markdown
"""

import os
import json

from . import config


def export_all():
    """读取 JSON 数据 → 生成 .md 文件"""
    BASE = config.BASE_DIR

    # 读取数据
    summaries_path = os.path.join(BASE, "course_summaries", "_all_summaries.json")
    kb_path = os.path.join(BASE, "knowledge_base", "knowledge_base.json")
    tools_path = os.path.join(BASE, "assets", "assets_tools.json")
    websites_path = os.path.join(BASE, "assets", "assets_websites.json")
    skills_path = os.path.join(BASE, "assets", "assets_skills.json")

    if not os.path.exists(summaries_path):
        print(f"⚠ 未找到数据，请先运行 pipeline。\n   缺失: {summaries_path}")
        return

    with open(summaries_path) as f:
        summaries = json.load(f)
    with open(kb_path) as f:
        knowledge = json.load(f)
    with open(tools_path) as f:
        tools = json.load(f)
    with open(websites_path) as f:
        websites = json.load(f)
    with open(skills_path) as f:
        skills = json.load(f)

    courses_dir = os.path.join(BASE, "📚 课程总结")
    assets_dir = os.path.join(BASE, "📦 资产库")
    os.makedirs(courses_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    # ── 课程总结 ──
    for s in summaries:
        title = s["course_title"].replace("/", "-").replace(":", "：")
        md = f"""---
tags: [课程总结, FemAI]
---

# {title}

## 📝 课程概要

{s['summary']}

"""
        if s.get("key_points"):
            md += "## 🎯 核心知识点\n\n"
            for i, kp in enumerate(s["key_points"], 1):
                md += f"{i}. {kp}\n"
            md += "\n"

        if s.get("key_takeaways"):
            md += "## 💡 关键 takeaways\n\n"
            for i, kt in enumerate(s["key_takeaways"], 1):
                md += f"{i}. **{kt}**\n"
            md += "\n"

        if s.get("tools_mentioned"):
            md += "## 🛠 工具与软件\n\n"
            for t in s["tools_mentioned"]:
                md += f"- {t}\n"
            md += "\n"

        if s.get("skills_learned"):
            md += "## 💪 学到技能\n\n"
            for sk in s["skills_learned"]:
                md += f"- {sk}\n"
            md += "\n"

        if s.get("recommended_resources"):
            md += "## 📎 推荐资源\n\n"
            if s["recommended_resources"].get("tools"):
                md += "### 推荐工具\n"
                for t in s["recommended_resources"]["tools"]:
                    md += f"- {t}\n"
                md += "\n"
            if s["recommended_resources"].get("websites"):
                md += "### 推荐网站\n"
                for w in s["recommended_resources"]["websites"]:
                    md += f"- {w}\n"
                md += "\n"

        if s.get("source_files"):
            md += "## 📁 原始文件\n\n"
            for f_src in s["source_files"]:
                md += f"- `{f_src}`\n"

        fname = "".join(c for c in title if c.isalnum() or c in "_ -（）()").strip()
        fname = fname.replace(" ", "_")
        with open(os.path.join(courses_dir, f"{fname}.md"), "w", encoding="utf-8") as f:
            f.write(md)

    # ── 工具清单 ──
    md = "---\ntags: [资产库, 工具]\n---\n\n# 🛠 全部工具清单\n\n| # | 工具名称 | 出现次数 | 来源课程 |\n|---|---------|---------|---------|\n"
    for i, t in enumerate(tools, 1):
        sources = ", ".join(t["sources"][:5])
        if len(t["sources"]) > 5:
            sources += f" ... (+{len(t['sources'])-5})"
        md += f"| {i} | **{t['name']}** | {t['count']} | {sources} |\n"
    with open(os.path.join(assets_dir, "🛠 工具清单.md"), "w", encoding="utf-8") as f:
        f.write(md)

    # ── 网站清单 ──
    md = "---\ntags: [资产库, 网站]\n---\n\n# 🌐 全部网站清单\n\n| # | 网站 | 出现次数 | 来源课程 |\n|---|------|---------|---------|\n"
    for i, w in enumerate(websites, 1):
        sources = ", ".join(w["sources"][:5])
        if len(w["sources"]) > 5:
            sources += f" ... (+{len(w['sources'])-5})"
        md += f"| {i} | [{w['name']}]({w['name']}) | {w['count']} | {sources} |\n"
    with open(os.path.join(assets_dir, "🌐 网站清单.md"), "w", encoding="utf-8") as f:
        f.write(md)

    # ── 技能清单 ──
    md = "---\ntags: [资产库, 技能]\n---\n\n# 💡 全部技能清单\n\n| # | 技能名称 | 出现次数 | 来源课程 |\n|---|---------|---------|---------|\n"
    for i, sk in enumerate(skills, 1):
        sources = ", ".join(sk["sources"][:5])
        if len(sk["sources"]) > 5:
            sources += f" ... (+{len(sk['sources'])-5})"
        md += f"| {i} | **{sk['name']}** | {sk['count']} | {sources} |\n"
    with open(os.path.join(assets_dir, "💡 技能清单.md"), "w", encoding="utf-8") as f:
        f.write(md)

    # ── 知识库条目 ──
    md = f"---\ntags: [知识库]\n---\n\n# 📋 知识库全部条目\n\n共 {len(knowledge)} 条知识条目。\n\n"
    for i, k in enumerate(knowledge, 1):
        md += f"---\n\n### {i}. {k.get('title', 'Untitled')}\n\n"
        md += f"**来源**: {k.get('source', 'unknown')}\n\n"
        md += k.get('summary', '') + "\n\n"
        if k.get("key_points"):
            md += "**知识点**:\n" + "\n".join(f"- {kp}" for kp in k["key_points"]) + "\n\n"
        if k.get("key_takeaways"):
            md += "**Takeaways**:\n" + "\n".join(f"- {kt}" for kt in k["key_takeaways"]) + "\n\n"
        entities = k.get("entities", {})
        if entities.get("tools"):
            md += "**工具**: " + ", ".join(entities["tools"]) + "\n\n"
        if entities.get("websites"):
            md += "**网站**:\n" + "\n".join(f"- {w}" for w in entities["websites"]) + "\n\n"
        if entities.get("skills"):
            md += "**技能**: " + ", ".join(entities["skills"]) + "\n\n"
    with open(os.path.join(BASE, "📋 知识库条目.md"), "w", encoding="utf-8") as f:
        f.write(md)

    # ── 总览索引 ──
    course_links = ""
    for s in summaries:
        title = s["course_title"]
        fname = "".join(c for c in title if c.isalnum() or c in "_ -（）()").strip().replace(" ", "_")
        course_links += f"  - [📖 {title}](%F0%9F%93%9A%20%E8%AF%BE%E7%A8%8B%E6%80%BB%E7%BB%93/{fname}.md)\n"

    index = f"""---
tags: [总览, FemAI]
---

# 🏠 FemAI 学习知识库

> FemAI Vol.2 课程知识库 · 自动构建

---

## 📚 课程总结

{course_links}
## 📦 资产库

  - [🛠 工具清单](%F0%9F%93%A6%20%E8%B5%84%E4%BA%A7%E5%BA%93/%F0%9F%9B%A0%20%E5%B7%A5%E5%85%B7%E6%B8%85%E5%8D%95.md)（{len(tools)} 个工具）
  - [🌐 网站清单](%F0%9F%93%A6%20%E8%B5%84%E4%BA%A7%E5%BA%93/%F0%9F%8C%90%20%E7%BD%91%E7%AB%99%E6%B8%85%E5%8D%95.md)（{len(websites)} 个网站）
  - [💡 技能清单](%F0%9F%93%A6%20%E8%B5%84%E4%BA%A7%E5%BA%93/%F0%9F%92%A1%20%E6%8A%80%E8%83%BD%E6%B8%85%E5%8D%95.md)（{len(skills)} 个技能）

## 📋 全部数据

  - [📋 知识库条目](%F0%9F%93%8B%20%E7%9F%A5%E8%AF%86%E5%BA%93%E6%9D%A1%E7%9B%AE.md)（{len(knowledge)} 条）
  - [📖 使用手册](KNOWLEDGE_BASE_MANUAL.md)

---

## 📊 快速统计

| 指标 | 数量 |
|------|:----:|
| 课程数 | {len(summaries)} |
| 知识条目 | {len(knowledge)} |
| 工具数 | {len(tools)} |
| 网站数 | {len(websites)} |
| 技能数 | {len(skills)} |

### 🔥 Top 5 最常用工具

"""
    for t in tools[:5]:
        index += f"- **{t['name']}** — 出现在 {t['count']} 节课\n"
    index += "\n### 🔥 Top 5 最常用技能\n\n"
    for sk in skills[:5]:
        index += f"- **{sk['name']}** — 出现在 {sk['count']} 节课\n"

    index += "\n---\n> 自动构建 · 知识库 Pipeline · 运行 `python3 -m pipeline.export_markdown` 更新\n"

    with open(os.path.join(BASE, "🏠 知识库总览.md"), "w", encoding="utf-8") as f:
        f.write(index)

    print(f"✅ 导出完成:")
    print(f"   📚 课程总结/ — {len(summaries)} 个文件")
    print(f"   📦 资产库/   — 3 个文件")
    print(f"   📋 知识库条目 — 1 个文件")
    print(f"   🏠 总览索引  — 1 个文件")


if __name__ == "__main__":
    export_all()
