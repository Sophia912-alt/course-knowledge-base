# 📚 Course Knowledge Base Pipeline

> 自动整理课程资料 → 生成结构化知识库 → 提取工具/网站/技能 → 生成每节课总结 → 导出 Obsidian 笔记

一个将课程学习资料转化为可积累、可检索的知识资产系统的工具。零门槛上手：拖入文件 → 双击脚本 → 在 Obsidian 中阅读。

[English](#english) | [中文](#中文)

---

## 中文

### 它能做什么

每次上完课，把课件（.md）和录音转写（.txt）放进对应文件夹，系统会自动：

| 步骤 | 说明 |
|------|------|
| 🧹 清洗 | 自动去噪、统一格式 |
| 🧠 知识提取 | AI 分析内容，提取核心知识点和结论 |
| 📝 课程总结 | 每节课生成独立笔记（含 key takeaways） |
| 📦 资产归类 | 所有工具、网站、技能自动归类为清单 |
| 📤 导出 | 生成 Obsidian 可直接打开的 `.md` 文件 |

### 快速开始

```bash
# 1. 下载项目
git clone https://github.com/YOUR_USER/course-knowledge-base.git
cd course-knowledge-base

# 2. 安装依赖
pip3 install requests

# 3. 配置 API Key
#    编辑 run_pipeline_with_key.sh，填入你的 API Key

# 4. 放入课件
#    将 .md 课件拖入 raw-slides/
#    将 .txt 转写拖入 raw-transcripts/

# 5. 运行
bash run_pipeline_with_key.sh

# 6. 用 Obsidian 打开项目文件夹阅读
```

### 项目结构

```
├── raw-slides/              ← 放课件 .md（手动）
├── raw-transcripts/         ← 放转写 .txt（手动）
├── raw-feishu/              ← 放群聊导出（可选）
├── pipeline/                ← 核心代码
│   ├── config.py            ← 配置文件
│   ├── ingestion.py         ← 数据导入
│   ├── cleaning.py          ← 数据清洗
│   ├── llm_client.py        ← AI 调用（带自动重试）
│   ├── knowledge_extraction.py  ← 知识提取
│   ├── course_summarization.py  ← 课程总结
│   ├── asset_extraction.py      ← 资产提取
│   └── export_markdown.py       ← Markdown 导出
├── run_pipeline.py          ← 主入口
└── run_pipeline_with_key.sh ← 带 Key 的运行脚本
```

输出（运行后自动生成）：

```
📚 课程总结/       ← 每节课的独立笔记
📦 资产库/         ← 工具/网站/技能清单
🏠 知识库总览.md   ← Obsidian 入口页
```

### 配置

编辑 `run_pipeline_with_key.sh`：

```bash
export OPENAI_API_KEY="sk-..."           # 你的 API Key
export OPENAI_BASE_URL="https://api.deepseek.com"  # API 地址
export PIPELINE_MODEL="deepseek-chat"    # 模型名称
```

支持任何 OpenAI 兼容 API（OpenAI / DeepSeek / 本地模型等）。

### 许可证

[MIT](LICENSE)

---

## English

A tool that turns your course materials into a searchable, accumulable knowledge asset system. Zero-code: drag in files → double-click to run → read in Obsidian.

### How It Works

After each class, put your slides (.md) and transcripts (.txt) into the folders. The system automatically:

| Step | Description |
|------|-------------|
| 🧹 Clean | Strip noise, unify format |
| 🧠 Extract | AI reads & extracts knowledge points |
| 📝 Summarize | One note per lesson with key takeaways |
| 📦 Classify | Tools, websites, skills become sorted lists |
| 📤 Export | Generates `.md` files for Obsidian |

### Quick Start

```bash
git clone https://github.com/YOUR_USER/course-knowledge-base.git
cd course-knowledge-base
pip3 install requests

# Edit run_pipeline_with_key.sh with your API key
# Put .md slides into raw-slides/
# Put .txt transcripts into raw-transcripts/

bash run_pipeline_with_key.sh
# Open the folder in Obsidian
```

### Configuration

Edit `run_pipeline_with_key.sh`:

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://api.deepseek.com"
export PIPELINE_MODEL="deepseek-chat"
```

Works with any OpenAI-compatible API.

### Requirements

- Python 3.8+
- `requests` library
- An API key for LLM access (OpenAI / DeepSeek / etc.)

### License

[MIT](LICENSE)
