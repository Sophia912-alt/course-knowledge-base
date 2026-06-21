"""
course_summarization.py — 课程级总结

为每一节课生成独立的结构化总结文件，存入 course_summaries/。
"""

import os
import json
import re

from . import config
from .utils import write_json, safe_filename, read_json
from .llm_client import LLMClient


# 课程归组函数：将 source 映射到统一的课程名
# 默认使用源文件名作为课程名，用户可在 config.py 中自定义映射
COURSE_MAP = {}  # 由用户覆盖

# 课程与源文件的关系（自动推断）
# 同名 slides 和 transcript 会被归到同一课程下


def _group_by_course(knowledge: list[dict], clean_records: list[dict]) -> dict:
    """
    将 knowledge 和 clean_records 按课程归组
    返回: { course_title: {"knowledge": [...], "slides": [...], "transcripts": [...]} }
    """
    groups = {}

    # 归并 knowledge
    for k in knowledge:
        raw_source = k.get("source", "")
        course = COURSE_MAP.get(raw_source, raw_source)
        groups.setdefault(course, {"knowledge": [], "slides": [], "transcripts": []})
        groups[course]["knowledge"].append(k)

    # 归并 clean_records 中的 slides/transcripts
    for r in clean_records:
        raw_source = r.get("source", "")
        course = COURSE_MAP.get(raw_source, raw_source)
        groups.setdefault(course, {"knowledge": [], "slides": [], "transcripts": []})
        rtype = r.get("type", "")
        if rtype == "slides":
            groups[course]["slides"].append(r)
        elif rtype == "transcript":
            groups[course]["transcripts"].append(r)

    return groups


COURSE_SUMMARY_SYSTEM = """你是一位教育分析专家。请基于提供的多源课程资料（课件+转写+结构化知识），为这节课生成完整的课程总结。

严格按以下 JSON 格式输出：

{
  "course_title": "课程名称",
  "summary": "课程整体内容概括（3-5句话）",
  "key_points": ["知识结构拆解要点1", "要点2", ...],
  "key_takeaways": ["最重要的结论1（必须提炼，不可重复内容）", ...],
  "tools_mentioned": ["工具名称1", ...],
  "skills_learned": ["技能1", ...],
  "recommended_resources": {
    "tools": ["工具推荐", ...],
    "websites": ["网站推荐", ...]
  },
  "source_files": ["slides/xxx.md", "transcripts/xxx.txt"]
}

注意：
- key_takeaways 是这门课最重要的 3-7 条结论，必须提炼，不能复述原文
- recommended_resources 中只收录老师或同学在课程中推荐的工具和网站
- source_files 列出对应的原始文件来源"""


def generate_course_summary(course_title: str, group: dict,
                            clean_records: list[dict]) -> dict:
    """对单个课程生成总结，使用 LLM + 启发式兜底"""
    knowledge = group.get("knowledge", [])
    slides = group.get("slides", [])
    transcripts = group.get("transcripts", [])

    # 构建 LLM 输入
    parts = []

    if slides:
        parts.append("=== 课件内容 ===")
        for s in slides:
            c = s.get("content", "")
            parts.append(f"[{s.get('source', '')}]")
            parts.append(c[:6000])  # 每份课件截断

    if transcripts:
        parts.append("\n=== 转写内容 ===")
        for t in transcripts:
            c = t.get("content", "")
            parts.append(f"[{t.get('source', '')}]")
            parts.append(c[:8000])

    if knowledge:
        parts.append("\n=== 已有结构化知识 ===")
        for k in knowledge:
            parts.append(json.dumps(k, ensure_ascii=False, indent=2))

    full_text = "\n\n".join(parts)

    # 如果太长，截断
    if len(full_text) > 25000:
        full_text = full_text[:25000] + "\n\n[... 截断 ...]"

    # 源文件列表
    source_files = []
    for s in slides:
        source_files.append(f"slides/{s.get('source', '')}")
    for t in transcripts:
        source_files.append(f"transcripts/{t.get('source', '')}")
    source_files = list(set(source_files))

    # LLM 生成
    try:
        client = LLMClient()
        user_prompt = f"请为以下课程「{course_title}」生成总结。\n\n{full_text}"
        result = client.chat_json(COURSE_SUMMARY_SYSTEM, user_prompt)
        result["source_files"] = source_files
        return result
    except Exception as e:
        print(f"    ⚠ LLM 生成失败，使用启发式兜底: {e}")
        # 启发式兜底
        all_tools = set()
        all_skills = set()
        all_websites = set()
        all_points = []
        all_takeaways = []

        for k in knowledge:
            entities = k.get("entities", {})
            all_tools.update(entities.get("tools", []))
            all_skills.update(entities.get("skills", []))
            all_websites.update(entities.get("websites", []))
            all_points.extend(k.get("key_points", []))
            all_takeaways.extend(k.get("key_takeaways", []))

        # 从 slides 文本正则提取
        for s in slides:
            from .utils import extract_entities_from_text
            tools, websites, skills = extract_entities_from_text(s.get("content", ""))
            all_tools.update(tools)
            all_skills.update(skills)
            all_websites.update(websites)

        return {
            "course_title": course_title,
            "summary": f"课程 {course_title} (启发式总结)",
            "key_points": all_points[:10] if all_points else [],
            "key_takeaways": all_takeaways[:7] if all_takeaways else ["（LLM 不可用，未生成 key takeaways）"],
            "tools_mentioned": sorted(all_tools),
            "skills_learned": sorted(all_skills),
            "recommended_resources": {
                "tools": [],
                "websites": sorted(all_websites)[:10],
            },
            "source_files": source_files,
        }


def run_course_summarization(knowledge: list[dict] = None,
                              clean_records: list[dict] = None) -> list[dict]:
    """执行为每节课生成总结"""
    if knowledge is None:
        kb_path = os.path.join(config.KNOWLEDGE_BASE_DIR, "knowledge_base.json")
        if os.path.exists(kb_path):
            knowledge = read_json(kb_path)
        else:
            raise FileNotFoundError(f"未找到知识库: {kb_path}")

    if clean_records is None:
        all_path = os.path.join(config.PROCESSED_DIR, "clean_all.json")
        if os.path.exists(all_path):
            clean_records = read_json(all_path)
        else:
            clean_records = []

    print("\n" + "=" * 50)
    print("📋 [Step 4] Course Summarization — 课程级总结")
    print("=" * 50)

    groups = _group_by_course(knowledge, clean_records)
    print(f"  识别到 {len(groups)} 节课: {list(groups.keys())}")

    summaries = []
    os.makedirs(config.COURSE_SUMMARIES_DIR, exist_ok=True)

    for course_title, group in sorted(groups.items()):
        print(f"\n  📖 生成总结: {course_title}")
        summary = generate_course_summary(course_title, group, clean_records)
        summaries.append(summary)

        # 写入独立文件
        fname = safe_filename(course_title)
        out_path = os.path.join(config.COURSE_SUMMARIES_DIR, f"{fname}.json")
        write_json(summary, out_path)
        print(f"    ✅ 已保存: {out_path}")

    # 也写入全量
    all_path = os.path.join(config.COURSE_SUMMARIES_DIR, "_all_summaries.json")
    write_json(summaries, all_path)
    print(f"\n  ✓ 课程总结全部完成: {len(summaries)} 节")
    print(f"    全量: {all_path}")

    return summaries
