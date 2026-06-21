"""
knowledge_extraction.py — 知识结构化层

使用 LLM 对 processed 中的数据进行结构化处理。
每条知识输出：
  {"type":"lesson|discussion","title":"","summary":"","key_points":[],"key_takeaways":[],"entities":{"tools":[],"websites":[],"skills":[]},"source":""}
"""

import os
import json

from . import config
from .utils import write_json, safe_filename, read_json
from .llm_client import LLMClient


def _truncate_content(text: str, max_chars: int = 12000) -> str:
    """截断过长文本以适配 LLM 上下文"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... 内容截断 ...]"


SYSTEM_PROMPT = """你是 FemAI 课程的知识分析师。你的任务是从课程资料中提取结构化知识。

请为以下课程内容提取知识，严格按照 JSON 格式输出：

{
  "type": "lesson",  // 始终为 "lesson"
  "title": "课程标题",
  "summary": "内容概要（2-4句）",
  "key_points": [
    "核心知识点1",
    "核心知识点2"
  ],
  "key_takeaways": [
    "最重要的结论/方法论（必须是提炼，不是复述原文）"
  ],
  "entities": {
    "tools": ["工具/API/软件名称", ...],
    "websites": ["网站/GitHub/文档链接", ...],
    "skills": ["技能/方法论/能力", ...]
  },
  "source": "来源标识"
}

注意：
- key_points：课程中的核心知识点拆解，3-10条
- key_takeaways：最重要的结论/方法论总结（必须提炼，不可复述原文），2-5条
- tools：所有工具/API/软件（提取具体名称）
- websites：所有网站/GitHub/文档（提取 URL 或名称）
- skills：所有技能/方法论/能力
- 如果某个字段没有内容，用空列表 []，不要省略字段"""


def extract_knowledge_slides(clean_records: list[dict]) -> list[dict]:
    """对 slides 类型清洗记录进行 LLM 知识提取"""
    print("\n  🎯 处理课件（slides）...")
    slides_records = [r for r in clean_records if r["type"] == "slides"]
    return _extract_batch(slides_records, "slides")


def extract_knowledge_transcripts(clean_records: list[dict]) -> list[dict]:
    """对 transcripts 类型清洗记录进行 LLM 知识提取"""
    print("\n  🎯 处理转写（transcripts）...")
    transcript_records = [r for r in clean_records if r["type"] == "transcript"]
    return _extract_batch(transcript_records, "transcript")


def extract_knowledge_feishu(clean_records: list[dict]) -> list[dict]:
    """对 feishu 类型清洗记录进行 LLM 知识提取"""
    print("\n  🎯 处理飞书群聊（feishu）...")
    feishu_records = [r for r in clean_records if r["type"] == "feishu"]
    return _extract_batch(feishu_records, "feishu")


def _extract_batch(records: list[dict], label: str) -> list[dict]:
    """批量提取知识"""
    if not records:
        print(f"    (无 {label} 数据)")
        return []

    client = LLMClient()
    results = []

    for i, record in enumerate(records):
        content = record["content"]
        source = record["source"]
        truncated = _truncate_content(content)
        print(f"    [{i+1}/{len(records)}] {source} ({len(content)} chars)... ", end="")

        user_prompt = f"""请分析以下课程内容，提取结构化知识。

来源: {source}

内容:
{truncated}"""

        try:
            knowledge = client.chat_json(SYSTEM_PROMPT, user_prompt)
            knowledge["source"] = source  # 确保 source 正确
            results.append(knowledge)
            print("✅")
        except Exception as e:
            print(f"❌ {e}")
            # 用启发式兜底
            from .utils import extract_entities_from_text
            tools, websites, skills = extract_entities_from_text(content)
            results.append({
                "type": "lesson",
                "title": source,
                "summary": f"(LLM 提取失败: {e})",
                "key_points": [],
                "key_takeaways": [],
                "entities": {
                    "tools": tools,
                    "websites": websites,
                    "skills": skills,
                },
                "source": source,
            })

    return results


def run_knowledge_extraction(clean_records: list[dict] = None) -> list[dict]:
    """执行完整知识提取流程"""
    if clean_records is None:
        # 从 processed 读取
        all_path = os.path.join(config.PROCESSED_DIR, "clean_all.json")
        if os.path.exists(all_path):
            clean_records = read_json(all_path)
        else:
            raise FileNotFoundError(f"未找到清洗数据: {all_path}")

    print("\n" + "=" * 50)
    print("🧠 [Step 3] Knowledge Extraction — 知识结构化")
    print("=" * 50)

    all_knowledge = []
    all_knowledge.extend(extract_knowledge_slides(clean_records))
    all_knowledge.extend(extract_knowledge_transcripts(clean_records))
    all_knowledge.extend(extract_knowledge_feishu(clean_records))

    # 保存
    os.makedirs(config.KNOWLEDGE_BASE_DIR, exist_ok=True)
    out_path = os.path.join(config.KNOWLEDGE_BASE_DIR, "knowledge_base.json")
    write_json(all_knowledge, out_path)

    print(f"\n  ✓ 知识库生成: {len(all_knowledge)} 条知识")
    print(f"    保存至: {out_path}")

    return all_knowledge
