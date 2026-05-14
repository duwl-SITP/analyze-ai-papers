# Analyze AI Papers

This is the `analyze-ai-papers` skill repository — a structured workflow for reading and analyzing AI research papers.

## Skill Invocation

Slash command (project-level):

```
/analyze-ai-papers [paper path or request]
```

Or reference explicitly in a prompt:

```
Use $analyze-ai-papers to summarize this paper: /path/to/paper.pdf
```

## Key Files

- `SKILL.md` — complete workflow, routing rules, and reporting contract
- `references/` — analysis rubric, language rules, domain cues, and extraction guidance
- `assets/templates/` — structured markdown report templates
- `scripts/extract_pdf_figures.py` — PDF figure/table extraction helper

## Optional Dependencies

Required only for PDF figure/table extraction:

```bash
python3 -m pip install pymupdf pdfplumber
```
