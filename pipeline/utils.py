"""
共享工具函数
"""

import json
import os
import glob
import re


def ensure_dirs(dirs: list[str]):
    """确保所有目录存在"""
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def list_files(directory: str, pattern: str) -> list[str]:
    """列出目录下匹配 pattern 的所有文件（按名称排序）"""
    return sorted(glob.glob(os.path.join(directory, pattern)))


def read_file_text(path: str) -> str:
    """读取文件全部文本"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_json(obj, path: str, indent: int = 2):
    """写入 JSON 文件"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)


def read_json(path: str):
    """读取 JSON 文件"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_filename(name: str) -> str:
    """将任意字符串转换为安全的文件名"""
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = re.sub(r'\s+', '_', name)
    name = name.strip('._')
    return name or "untitled"


def extract_entities_from_text(text: str) -> tuple[list[str], list[str], list[str]]:
    """
    从文本中初步提取工具/网站/技能（正则启发式）
    返回 (tools, websites, skills) 各列表
    """
    # 网站
    websites = re.findall(r'https?://[^\s)\]]+', text)
    websites = list(set(w.rstrip('.,;:!?)') for w in websites))

    # 常见工具关键词（粗略）
    tool_keywords = [
        "codex", "claude", "hermes", "openai", "chatgpt", "deepseek", "obsidian",
        "github", "vscode", "cursor", "cc-switch", "ccswitch",
        "hyperframes", "lovart", "tiktokenizer",
    ]
    tools = []
    for kw in tool_keywords:
        if re.search(kw, text, re.IGNORECASE):
            # 尝试取精确名称
            m = re.search(r'(?<![a-zA-Z])' + re.escape(kw) + r'(?![a-zA-Z])', text, re.IGNORECASE)
            if m:
                tools.append(kw)

    # 技能关键词
    skill_keywords = [
        "prompt engineering", "prompt", "vibe coding", "workflow", "数据分析",
        "内容创作", "build in public", "项目管理", "AI 编程", "vibe coding",
        "知识库", "obsidian", "飞书 bot", "feishu cli",
    ]
    skills_list = [s for s in skill_keywords if s.lower() in text.lower()]

    return tools, websites, skills_list
