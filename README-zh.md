# Analyze AI Papers

> 📘 一个可同时用于 Codex 与 Claude Code 的论文分析工作流。

`analyze-ai-papers` 用于把 AI 研究论文转成结构化、证据约束明确的分析结果。它适合做整篇论文阅读、方法拆解、实验解读和参考文献关联分析，而不是只基于标题或摘要的简略总结。

## 兼容性

- **Codex**：通过 `SKILL.md` 作为本地 skill 使用
- **Claude Code**：通过 `.claude/commands/analyze-ai-papers.md` 作为项目斜杠命令使用，并通过 `CLAUDE.md` 提供项目级记忆；clone 完整仓库并创建指向它的命令文件可全局使用

## Highlights

- 📄 面向 AI 研究论文的结构化 markdown 分析
- 🧠 重点覆盖方法、公式、训练设置、实验、消融和局限性
- ✍️ 输出风格正式、技术化、偏实现导向
- 🖼️ 仅在确有需要时提取 figures / tables
- 🧩 支持 born-digital 学术 PDF、arXiv PDF，以及配合 MinerU 的扫描版 PDF

## 适用场景

当你希望自己的编码助手完成以下任务时，可以使用这个仓库：

- 对论文做技术性较强的总结
- 解释核心方法或创新点
- 分析实验结果与消融实验
- 对比论文与前作的差异
- 在需要时，将 PDF 转成带本地图表资源的 markdown

默认工作流是**文本优先**。图表提取属于辅助路径，不是默认主行为。

## 安装方式

这个仓库支持两种使用方式：

- 安装成 **Codex skill**
- 直接作为 **Claude Code 项目仓库** 使用

### 在 Codex 中使用

将仓库放到本地 skills 目录中。

推荐安装到以下位置之一：

- `$CODEX_HOME/skills/analyze-ai-papers`
- `~/.codex/skills/analyze-ai-papers`

例如：

```bash
mkdir -p ~/.codex/skills
cp -r analyze-ai-papers ~/.codex/skills/
```

Codex 必需入口文件：

- `SKILL.md`

### 在 Claude Code 中使用

这个仓库同时支持 Claude Code 的项目 skill 和个人全局 skill。

项目内使用：

- 直接在 Claude Code 中打开这个仓库
- Claude Code 会自动读取仓库根目录下的 `CLAUDE.md`
- `/analyze-ai-papers` 斜杠命令通过 `.claude/commands/analyze-ai-papers.md` 生效

全局个人命令用法：

`SKILL.md` 运行时会读取 `references/` 和 `assets/templates/` 下的文件，单独复制一个文件无法工作。需要将整个仓库 clone 到固定位置，再创建一个指向该位置的命令文件。

```bash
# 1. 将仓库 clone 到固定位置
git clone <repo-url> ~/.claude/skills/analyze-ai-papers

# 2. 创建全局命令文件
cat > ~/.claude/commands/analyze-ai-papers.md << 'EOF'
---
description: Read, analyze, and summarize AI research papers from PDFs, arXiv papers, excerpts, figures, or tables
argument-hint: [paper path or request]
---

Skill files are at ~/.claude/skills/analyze-ai-papers/.
Read ~/.claude/skills/analyze-ai-papers/SKILL.md and follow its complete workflow, routing rules, and reporting contract exactly. When the skill instructs you to read a file under references/ or assets/templates/, read it from ~/.claude/skills/analyze-ai-papers/. Apply it to: $ARGUMENTS
EOF
```

安装后在任意项目中均可使用 `/analyze-ai-papers`。

Claude 侧入口文件：

- `CLAUDE.md`
- `.claude/commands/analyze-ai-papers.md`（项目级斜杠命令）
- `~/.claude/commands/analyze-ai-papers.md`（全局个人命令，需手动创建）

### 核心文件

这个仓库的核心共享文件包括：

- `references/`
- `assets/templates/`
- `scripts/extract_pdf_figures.py`

### 可选 Python 依赖

普通论文分析本身不依赖提取脚本。  
如果你需要使用 PDF 图表提取或 PDF 转 markdown，请安装：

```bash
python3 -m pip install pymupdf pdfplumber
```

可选：

- 如果你希望处理扫描版 PDF，并先生成 OCR/markdown 骨架，可以额外安装 MinerU。

## Quick Start

### 普通论文分析

英文示例：

```text
Use $analyze-ai-papers and summarize this paper in English:
/path/to/paper.pdf
```

中文示例：

```text
使用 $analyze-ai-papers，用中文详细总结这篇论文：
/path/to/paper.pdf
```

在 Claude Code 中，也可以直接这样调用：

```text
/analyze-ai-papers 用中文总结 /path/to/paper.pdf
```

通常会输出一份结构化 markdown 报告，内容包括：

- 论文基本信息
- 核心问题与主要贡献
- 方法概述与技术细节
- 实验设置
- 主实验结果与消融实验
- 优点、缺点与局限性
- 相关工作与参考文献

如果你希望指定输出语言，只需要在提示词中直接说明；如果没有显式指定，工作流会默认使用用户的主要语言。

### 提取图表

提示词示例：

```text
Use $analyze-ai-papers to extract figures and tables from this PDF and produce markdown with local image links:
/path/to/paper.pdf
```

直接调用脚本：

```bash
python3 scripts/extract_pdf_figures.py \
  --pdf /path/to/paper.pdf \
  --out-dir /path/to/output_dir
```

如果你已经有 MinerU 生成的 markdown 骨架：

```bash
python3 scripts/extract_pdf_figures.py \
  --pdf /path/to/paper.pdf \
  --skeleton-markdown /path/to/mineru.md \
  --out-dir /path/to/output_dir
```

输出内容：

- `paper.md` 或你指定名称的 markdown 文件
- `images/` 目录，存放提取出的 figure/table 图片

## 图表提取说明

对于 born-digital PDF，当前表格提取默认采用 `pdfplumber` 生成基础候选框，再结合 `PyMuPDF` 的文本块和绘图对象做区域修正，然后执行页面区域渲染裁剪。

## 项目结构

- `.claude/commands/analyze-ai-papers.md`：Claude Code 项目级斜杠命令，触发时读取 `SKILL.md`
- `CLAUDE.md`：供 Claude Code 使用的项目级指令文件
- `SKILL.md`：skill 主说明与路由逻辑
- `references/`：分析规则、语言规则与 PDF 提取说明
- `assets/templates/`：markdown 报告模板
- `scripts/extract_pdf_figures.py`：PDF 图表提取脚本

## 说明

- 这个仓库针对的是 AI 研究论文，不是通用文档摘要工具。
- 默认工作流是论文阅读与分析，不是 PDF 资源提取。
- 对扫描版 PDF，章节层级质量很大程度上取决于 OCR 或 markdown 骨架来源。
- 论文标题、模型名、作者名、引用信息等专有名词，在合适情况下会保留原文形式。
