#!/usr/bin/env python3
"""
run_pipeline.py — FemAI 学习知识库 Pipeline 统一入口

执行顺序:
  raw → processed → knowledge_base → course_summaries → assets

用法:
  python run_pipeline.py              # 完整执行
  python run_pipeline.py --steps 1    # 只执行第 1 步
  python run_pipeline.py --steps 1,2  # 执行第 1 和 2 步
  python run_pipeline.py --skip-llm   # 跳过 LLM 调用（用启发式代替）
"""

import sys
import time
import os

# 确保 pipeline 包可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import config
from pipeline.utils import ensure_dirs
from pipeline.ingestion import run_ingestion
from pipeline.cleaning import process_ingested_data
from pipeline.knowledge_extraction import run_knowledge_extraction
from pipeline.course_summarization import run_course_summarization
from pipeline.asset_extraction import run_asset_extraction


PIPELINE_STEPS = [
    ("Ingestion", "raw → ingestion"),
    ("Cleaning", "ingestion → processed"),
    ("Knowledge Extraction", "processed → knowledge_base"),
    ("Course Summarization", "knowledge_base → course_summaries"),
    ("Asset Extraction", "knowledge_base → assets"),
]


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="FemAI 学习知识库 Pipeline")
    parser.add_argument("--steps", type=str, default="1,2,3,4,5",
                        help="要执行的步骤序号，逗号分隔 (1-5)")
    parser.add_argument("--skip-llm", action="store_true",
                        help="跳过 LLM 调用（使用启发式处理）")
    return parser.parse_args()


def run_pipeline(selected_steps: set[int], skip_llm: bool = False):
    """执行选中的 pipeline 步骤"""

    print("╔══════════════════════════════════════════════════════════╗")
    print("║     课程知识库 Pipeline                                ║")
    print(f"║     {config.BASE_DIR:<48}║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  步骤选择: {', '.join(str(s) for s in sorted(selected_steps))}")
    print(f"  LLM 模式: {'跳过 (启发式)' if skip_llm else '使用 API'}")
    print()

    # 确保目录存在
    ensure_dirs(config.ALL_DIRS)

    data = {}
    clean_records = None
    knowledge = None
    summaries = None
    assets = None

    step_times = []

    # ── Step 1: Ingestion ──
    if 1 in selected_steps:
        t0 = time.time()
        data = run_ingestion()
        step_times.append(("1. Ingestion", time.time() - t0))
    else:
        print("⏭ [Step 1] Ingestion — 跳过")

    # ── Step 2: Cleaning ──
    if 2 in selected_steps:
        t0 = time.time()
        clean_records = process_ingested_data(data if data else {})
        step_times.append(("2. Cleaning", time.time() - t0))
    else:
        print("⏭ [Step 2] Cleaning — 跳过")

    # ── Step 3: Knowledge Extraction ──
    if 3 in selected_steps:
        t0 = time.time()
        if skip_llm:
            # 跳过 LLM，用启发式直接提取
            print("\n" + "=" * 50)
            print("🧠 [Step 3] Knowledge Extraction — 启发式模式 (跳过 LLM)")
            print("=" * 50)
            from pipeline.utils import extract_entities_from_text
            import json

            if clean_records is None:
                from pipeline.utils import read_json
                clean_path = os.path.join(config.PROCESSED_DIR, "clean_all.json")
                clean_records = read_json(clean_path) if os.path.exists(clean_path) else []

            knowledge = []
            for r in clean_records:
                tools, websites, skills = extract_entities_from_text(r.get("content", ""))
                knowledge.append({
                    "type": "lesson",
                    "title": r.get("source", ""),
                    "summary": "(启发式提取 - 跳过 LLM)",
                    "key_points": [],
                    "key_takeaways": [],
                    "entities": {"tools": tools, "websites": websites, "skills": skills},
                    "source": r.get("source", ""),
                })

            from pipeline.utils import write_json
            os.makedirs(config.KNOWLEDGE_BASE_DIR, exist_ok=True)
            write_json(knowledge, os.path.join(config.KNOWLEDGE_BASE_DIR, "knowledge_base.json"))
            print(f"  ✓ 知识库生成 (启发式): {len(knowledge)} 条")
        else:
            knowledge = run_knowledge_extraction(clean_records)
        step_times.append(("3. Knowledge Extraction", time.time() - t0))
    else:
        print("⏭ [Step 3] Knowledge Extraction — 跳过")

    # ── Step 4: Course Summarization ──
    if 4 in selected_steps:
        t0 = time.time()
        summaries = run_course_summarization(knowledge, clean_records)
        step_times.append(("4. Course Summarization", time.time() - t0))
    else:
        print("⏭ [Step 4] Course Summarization — 跳过")

    # ── Step 5: Asset Extraction ──
    if 5 in selected_steps:
        t0 = time.time()
        assets = run_asset_extraction(knowledge)
        step_times.append(("5. Asset Extraction", time.time() - t0))
    else:
        print("⏭ [Step 5] Asset Extraction — 跳过")

    # ── 最终报告 ──
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║      Pipeline 执行完成                                  ║")
    print("╚══════════════════════════════════════════════════════════╝")

    for name, dur in step_times:
        print(f"  {name}: {dur:.1f}s")

    total = sum(d for _, d in step_times)
    print(f"  ⏱  总耗时: {total:.1f}s")

    print()
    print("  📂 输出目录:")
    print(f"     raw-slides/           → {len(os.listdir(config.RAW_SLIDES_DIR))} 文件")
    print(f"     raw-transcripts/      → {len(os.listdir(config.RAW_TRANSCRIPTS_DIR))} 文件")
    print(f"     raw-feishu/           → {len(os.listdir(config.RAW_FEISHU_DIR))} 文件")
    print(f"     processed/            → {len(os.listdir(config.PROCESSED_DIR))} 文件")
    print(f"     knowledge_base/       → {len(os.listdir(config.KNOWLEDGE_BASE_DIR))} 文件")
    print(f"     course_summaries/     → {len(os.listdir(config.COURSE_SUMMARIES_DIR))} 文件")
    print(f"     assets/               → {len(os.listdir(config.ASSETS_DIR))} 文件")
    print()

    return {
        "data": data,
        "clean_records": clean_records,
        "knowledge": knowledge,
        "summaries": summaries,
        "assets": assets,
    }


if __name__ == "__main__":
    args = parse_args()
    selected = set(int(s.strip()) for s in args.steps.split(",") if s.strip().isdigit())
    allowed = {1, 2, 3, 4, 5}
    selected &= allowed
    if not selected:
        print("❌ 请选择有效的步骤: 1-5")
        sys.exit(1)

    run_pipeline(selected, skip_llm=args.skip_llm)
