<p align="right">
  <a href="./README.md">English</a> | <a href="./README-zh.md">简体中文</a>
</p>

# Analyze AI Papers

> 📘 A paper-analysis workflow for Codex skills and Claude Code projects.

`analyze-ai-papers` turns AI research papers into structured, evidence-grounded reports. It is built for full-paper reading, method analysis, experiment interpretation, and reference-aware discussion rather than abstract-only summaries.

## Compatibility

- **Codex**: use this repository as a local skill via `SKILL.md`
- **Claude Code**: use this repository as a project with `.claude/commands/analyze-ai-papers.md` as the slash command and `CLAUDE.md` as project memory; clone the full repository and create a command file pointing to it for global use

## Highlights

- 📄 Read and analyze full AI research papers with a structured markdown output
- 🧠 Focus on methods, equations, training setup, experiments, ablations, and limitations
- ✍️ Keep the writing formal, technical, and implementation-oriented
- 🖼️ Extract figures and tables only when visuals are explicitly needed
- 🧩 Support born-digital academic PDFs, arXiv PDFs, and scanned PDFs with an optional MinerU skeleton

## What This Repository Is For

Use this repository when you want your coding agent to:

- summarize a paper in a technically rigorous way
- explain the core method or innovation
- analyze experiments and ablations
- compare a paper against prior work
- convert a paper PDF into markdown with local figure/table assets when necessary

By default, the workflow is text-first. Figure and table extraction are auxiliary paths, not the main behavior.

## Installation

This repository supports two usage modes:

- install it as a **Codex skill**
- open it directly in **Claude Code**

### Use with Codex

Install the repository into one of the following locations:

- `$CODEX_HOME/skills/analyze-ai-papers`
- `~/.codex/skills/analyze-ai-papers`

Example:

```bash
mkdir -p ~/.codex/skills
cp -r analyze-ai-papers ~/.codex/skills/
```

Required Codex entry file:

- `SKILL.md`

### Use with Claude Code

This repository supports both Claude Code project skills and Claude Code personal skills.

Project usage:

- Open the repository directly in Claude Code
- Claude Code will load the project memory file `CLAUDE.md`
- The `/analyze-ai-papers` slash command is available via `.claude/commands/analyze-ai-papers.md`

Global personal command usage:

`SKILL.md` reads supporting files under `references/` and `assets/templates/` at runtime, so copying a single file is not sufficient. Clone the full repository to a stable location and create a command file that points to it.

```bash
# 1. Clone the repository to a stable location
git clone <repo-url> ~/.claude/skills/analyze-ai-papers

# 2. Create the global command file
cat > ~/.claude/commands/analyze-ai-papers.md << 'EOF'
---
description: Read, analyze, and summarize AI research papers from PDFs, arXiv papers, excerpts, figures, or tables
argument-hint: [paper path or request]
---

Skill files are at ~/.claude/skills/analyze-ai-papers/.
Read ~/.claude/skills/analyze-ai-papers/SKILL.md and follow its complete workflow, routing rules, and reporting contract exactly. When the skill instructs you to read a file under references/ or assets/templates/, read it from ~/.claude/skills/analyze-ai-papers/. Apply it to: $ARGUMENTS
EOF
```

After this, `/analyze-ai-papers` is available in any project.

Claude-facing entry files:

- `CLAUDE.md`
- `.claude/commands/analyze-ai-papers.md` (project-level slash command)
- `~/.claude/commands/analyze-ai-papers.md` (global personal command, requires manual creation)

### Core files

The core shared files used by this repository are:

- `references/`
- `assets/templates/`
- `scripts/extract_pdf_figures.py`

### Optional Python dependencies

Paper analysis itself does not require the extraction script. If you want PDF figure/table extraction or PDF-to-markdown support, install:

```bash
python3 -m pip install pymupdf pdfplumber
```

Optional:

- Install MinerU separately if you want an OCR/markdown skeleton for scanned PDFs.

## Quick Start

### Analyze a paper

English:

```text
Use $analyze-ai-papers and summarize this paper in English:
/path/to/paper.pdf
```

Chinese:

```text
使用 $analyze-ai-papers，用中文详细总结这篇论文：
/path/to/paper.pdf
```

In Claude Code, the same skill can also be invoked directly as:

```text
/analyze-ai-papers summarize /path/to/paper.pdf in English
```

The workflow typically produces a structured markdown report covering:

- paper information
- core problem and contributions
- method overview and technical details
- experimental setup
- main results and ablations
- strengths, weaknesses, and limitations
- related work and references

If you want a specific output language, simply state it in the prompt. Otherwise, the workflow defaults to the user's primary language.

## Extraction Overview

For born-digital PDFs, table extraction currently uses `pdfplumber` for base table proposals and `PyMuPDF` for text/drawing-based region refinement before rendered-page cropping.

## Project Structure

- `.claude/commands/analyze-ai-papers.md`: Claude Code project-level slash command, reads `SKILL.md` on invocation
- `CLAUDE.md`: project instructions for Claude Code
- `SKILL.md`: core skill instructions and routing logic
- `references/`: analysis rules, language behavior, and PDF extraction guidance
- `assets/templates/`: markdown report templates
- `scripts/extract_pdf_figures.py`: PDF figure/table extraction helper

## Notes

- This repository is optimized for AI research papers, not general-purpose document summarization.
- The default workflow is paper reading and analysis, not PDF asset extraction.
- For scanned PDFs, section hierarchy quality depends heavily on the OCR or markdown backbone.
- Proper nouns such as paper titles, model names, author names, and citations are preserved in their original form when appropriate.
