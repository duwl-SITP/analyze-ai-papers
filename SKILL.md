---
name: analyze-ai-papers
description: Read, analyze, and summarize AI research papers from PDFs, arXiv papers, excerpts, figures, or tables. Use for full-paper summaries, method analysis, experiment and ablation interpretation, related-work comparison, and optional PDF figure/table extraction.
when_to_use: Trigger when the user provides a paper PDF, asks to explain a model or method section, compare against prior work, analyze experiments, or convert a paper PDF to markdown with local figure and table assets. Default to text-first analysis and use figure or table extraction only when explicitly requested or when visuals are necessary.
argument-hint: [request or paper path]
---

# Analyze AI Papers

Use this skill to produce evidence-grounded technical analysis of research papers. Its primary work is paper reading, summarization, and method analysis. PDF figure/table extraction is an auxiliary workflow, not the default path. Treat `output_language` as a first-class input parameter for any generated report or analytical writeup. Default to a structured markdown report with fairly detailed technical coverage, and shorten only when the user explicitly asks for a brief answer.

## Quick Start

1. Read the actual paper content before summarizing. Prefer the PDF, extracted text, appendix, supplemental material, or provided excerpts over metadata-only summaries.
2. Determine `output_language` before writing. If the user explicitly names a language, use it. If not, default to the user's primary language.
3. Read [references/output-language.md](references/output-language.md) whenever you will generate a report, explanation, experiment summary, strengths/weaknesses section, citation analysis, or future directions.
4. Read [references/math-markdown.md](references/math-markdown.md) whenever the final report will contain equations, symbols, losses, scoring rules, or variable names from the paper.
5. Read [references/report-readability.md](references/report-readability.md) whenever the final report explains technical mechanisms, formulas, prompts, losses, constraints, variables, or model components.
6. State the evidence boundary up front when the input is incomplete. If only the title, abstract, or a partial section is available, say so and avoid inventing missing details.
7. Read [references/analysis-rubric.md](references/analysis-rubric.md) for the full analysis checklist.
8. Read [references/domain-cues.md](references/domain-cues.md) when the paper is in vision, multimodal modeling, detection, segmentation, video, domain adaptation, transformer architectures, or generative modeling.
9. Read [references/reference-mapping.md](references/reference-mapping.md) when the user asks about related work, references, or differences from prior work.
10. Read [references/pdf-figure-extraction.md](references/pdf-figure-extraction.md) only when the user explicitly asks to extract figures/tables or convert a PDF to markdown, or when figures/tables are necessary to explain architectures, modules, pipelines, qualitative comparisons, or dense result tables.
11. Use [assets/templates/full-paper-analysis.md](assets/templates/full-paper-analysis.md) as the default report skeleton. Use the narrower templates only when the user asks for an experiments-only or references-only output.

## Report Contract Layers

Use these files with clear ownership boundaries:

- `SKILL.md`: workflow, routing, and output-shape decisions
- `references/output-language.md`: canonical output-language policy
- `references/math-markdown.md`: canonical math-formatting policy
- `references/report-readability.md`: canonical paragraph-level readability and transition policy
- `references/analysis-rubric.md`: canonical detailed review checklist for the final report
- `assets/templates/*.md`: report skeletons and section placeholders
- `agents/openai.yaml`: concise default invocation prompt

## Task Routing

- The primary path is paper reading, summarization, method analysis, experiment analysis, and related-work analysis.
- Do not run `scripts/extract_pdf_figures.py` for a normal summary or method explanation unless visual material is actually needed.
- Use PDF figure/table extraction or PDF-to-markdown only when the user explicitly asks for it, or when figures/tables are necessary to help the user inspect network architectures, module composition, pipeline flow, qualitative examples, or key experimental tables.
- For PDF figure/table extraction or PDF-to-markdown tasks, read [references/pdf-figure-extraction.md](references/pdf-figure-extraction.md) first and use `scripts/extract_pdf_figures.py`.
- Within that extraction path, prefer `pdfplumber` base table proposals refined by `PyMuPDF` text/drawing analysis for born-digital PDFs.
- For any generated report or analytical markdown, follow the shared report contract in [references/output-language.md](references/output-language.md), [references/math-markdown.md](references/math-markdown.md), [references/report-readability.md](references/report-readability.md), and [references/analysis-rubric.md](references/analysis-rubric.md).
- If the user explicitly asks to regenerate, rerun, or re-extract, treat the task as a fresh run and do not reuse previously generated markdown, images, or report text as inputs.
- Prefer rendered-page region cropping over raw embedded-image extraction. This is more robust for vector figures, mixed raster/vector layouts, and multimodal research papers.
- For scanned PDFs or complex arXiv layouts, prefer a MinerU-generated markdown skeleton and then inject cropped figure/table images plus preserved captions into that markdown.

## Workflow

### 0. Plan persisted artifacts

- If the task will write files to disk, first determine the paper's main method name and use it as the artifact-folder name.
- If the paper's main method name cannot be identified reliably, fall back to the input PDF filename without the extension.
- Once a canonical artifact-folder name has been chosen, reuse that exact name for every preparatory directory, intermediate artifact, extraction run, and final report path.
- Create one method-named folder and keep all intermediate outputs and final outputs inside it, including extracted markdown, `images/`, and the final analytical report.
- When the user explicitly asks to regenerate, rerun extraction and report generation from the source paper instead of reusing existing generated files inside that folder.

### 1. Set `output_language`

- Treat `output_language` as a required logical input even when the user does not spell it out.
- Follow [references/output-language.md](references/output-language.md) for language selection, preserved source terms, and section-level consistency.

### 2. Establish the evidence boundary

- Identify what is actually available: full paper, appendix, supplemental, figures, tables, only title/abstract, or user excerpts.
- Say explicitly which parts were read.
- Treat missing details as unknown. Do not backfill them with likely-but-unverified claims.
- If the user asked for PDF asset extraction, state whether the PDF is born-digital or scanned and whether a MinerU markdown skeleton is available.

### 3. Decide whether visual extraction is needed

- Default to text-first analysis. Most summary and method-analysis tasks do not need figure extraction.
- Trigger the visual branch only when one of these is true:
  - the user explicitly asks for figures, tables, or PDF-to-markdown output
  - the question depends on architecture diagrams, module decomposition, pipeline flowcharts, qualitative examples, or dense result tables
  - a visual artifact would materially reduce ambiguity in the explanation
- If one figure or table is enough to support the explanation, prefer targeted extraction or targeted discussion over full PDF-to-markdown conversion.
- If no visual branch is needed, continue with the normal analysis workflow and do not run `scripts/extract_pdf_figures.py`.

### 4. Parse the paper structure

Extract the paper into the closest available versions of these units:

- Title, authors, venue/year if present
- Abstract
- Introduction
- Related work
- Method or approach
- Architecture or pipeline figures
- Loss or objective sections
- Optimization sections or experimental setup
- Main results
- Ablations or analysis
- Limitations or conclusion
- Appendix or supplemental details

If the paper uses unusual section names, map them to these functional roles instead of preserving superficial headings.

### 5. Identify the research problem and motivation

- State the target task and input/output setting precisely.
- Explain what gap in prior work the authors claim to address.
- Distinguish problem-level novelty from implementation-level improvement.
- Note whether the motivation is driven by accuracy, efficiency, robustness, generalization, data scarcity, cross-domain transfer, multimodal grounding, or generation quality.

### 6. Analyze the technical method

- Summarize the method at two levels:
  - a 3-5 sentence overview of the end-to-end pipeline
  - a component-level explanation of the architecture
- Default to detailed technical explanation rather than high-level prose. Expand the actual data flow, module interactions, tensor/representation transitions, supervision path, and inference path.
- Name the modules, information flow, representations, and supervision signals.
- Explain why each major component exists, not just what it is called.
- Organize `Technical Details` into small subsections grouped by the paper's main innovations. Do not write this section as one flat block when the method introduces several distinct ideas.
- In `Technical Details`, follow [references/report-readability.md](references/report-readability.md) for paragraph-level transitions and [references/analysis-rubric.md](references/analysis-rubric.md) for cause -> mechanism -> downstream effect expectations.
- Include key equations when they are central to the method, loss design, matching rule, optimization target, or inference score computation.
- Follow [references/math-markdown.md](references/math-markdown.md) for equation and symbol formatting.
- Use figures or extracted images when architecture diagrams, module composition, qualitative examples, or key tables materially help the user understand the method.
- Identify whether gains plausibly come from architecture, objective design, optimization, data engineering, pretraining, or inference-time heuristics.

### 7. Interpret equations and objectives

- Rewrite key equations in plain language.
- Define each loss term, constraint, regularizer, matching objective, or generative objective.
- Explain how the objective couples with the architecture and data pipeline.
- Call out training schedules, teacher-student updates, EMA, warmup, burn-in, multi-stage optimization, pseudo-labeling, retrieval steps, or auxiliary objectives.
- Follow [references/math-markdown.md](references/math-markdown.md) for math rendering and [references/report-readability.md](references/report-readability.md) for explaining why each equation appears and what role it plays.
- If the paper omits needed definitions, say what is underspecified.

### 8. Analyze experiments and ablations

- Record datasets, splits, metrics, baselines, compute regime, and the loss/optimization recipe together in the experimental setup discussion.
- Separate main benchmark results from controlled ablations.
- Identify what each ablation actually isolates.
- Include the paper's necessary visual evidence for experiments and ablations when tables, qualitative figures, failure cases, or comparison visualizations materially strengthen the interpretation.
- Explain what each included visualization demonstrates and how it supports or limits the empirical claim.
- Note whether improvements are broad or narrow: only on one dataset, only at large scale, only with extra data, only under a specific metric, or only with strong pretraining.
- Flag comparisons that may be unfair because of data, compute, resolution, pretraining, tuning budget, or implementation differences.

### 9. Evaluate strengths, weaknesses, and limitations

- Be concrete and tie each point to evidence from the paper.
- Discuss computational complexity, memory cost, inference latency, annotation burden, extra modules, dependence on pretraining, sensitivity to hyperparameters, and generalization assumptions.
- Prefer falsifiable observations over generic praise or criticism.

### 10. Analyze related work and references

- Prioritize cited papers that are direct baselines, borrowed components, methodological precedents, or comparison targets.
- Explain the role each reference plays in the argument: problem framing, architecture lineage, loss design, benchmark protocol, or comparison target.
- Write the related-work analysis as normal prose or compact bullets, not as per-reference metadata cards.
- Use a clean numbered reference list for the references subsection, not tables.
- Do not create separate “Foundational Works” or “Closest Prior Works” subsections unless the user explicitly asks for that categorization.

### 11. Generate research insights

- Extract what is reusable beyond the paper's headline result.
- Suggest plausible follow-up directions grounded in the method's actual bottlenecks.
- Separate paper claims from your own inference.

### 12. Write the output

- Use the report template headings unless the user requests a different format.
- Translate section titles and analysis prose into `output_language` while preserving the same section order and markdown structure.
- Keep terminology precise and implementation-oriented.
- Use a formal, written register. Avoid conversational, casual, or chatty phrasing.
- Preserve original paper titles, citations, model names, author names, and other proper nouns exactly unless the user explicitly asks for transliteration.
- Prefer short, dense paragraphs or compact bullets over vague summaries, but do not under-explain the technical core.
- Apply the detailed report contract from [references/output-language.md](references/output-language.md), [references/math-markdown.md](references/math-markdown.md), [references/report-readability.md](references/report-readability.md), and [references/analysis-rubric.md](references/analysis-rubric.md) rather than redefining those rules here.
- If the task writes files to disk, save the final report inside the same method-named artifact folder that contains the intermediate extraction outputs.
- Include formulas and images when they materially improve comprehension of the method, objective, architecture, or experimental evidence.
- Place formulas primarily in `Technical Details` and `Experimental Setup`. Place figures or image references primarily in `Architecture And Pipeline` and `Experimental Results`.
- In `Technical Details`, use innovation-based subheadings when the paper has multiple core ideas, and let each subsection cover one innovation's motivation, mechanism, and effect chain.
- If you used the visual branch, mention that explicitly and report what was extracted and why it was needed for the explanation.
- End with a one-sentence summary that captures problem, method, and main takeaway.

## Reporting Rules

- Treat [references/analysis-rubric.md](references/analysis-rubric.md) as the detailed final-check list for analytical quality.
- Attribute claims carefully:
  - "The paper claims..." for author assertions.
  - "The experiments show..." for reported evidence.
  - "A likely reason is..." for your inference.
- Do not call a result stronger than the evidence supports.
- Do not infer novelty from branding or naming alone.
- Do not treat ablations as proof of mechanism unless the ablation isolates that mechanism.
- If a figure is central to the method, describe the data flow in words.
- If a formula is central to the method or objective, include it or restate it explicitly instead of only alluding to it.
- If a visualization is central to the experimental claim or ablation interpretation, include it or refer to it explicitly and explain its evidentiary role.
- In the references section, use a numbered reference list with normal citation formatting rather than a table.
- Do not attach `Role`, `Confidence`, or similar per-reference metadata fields unless the user explicitly asks for that richer analysis format.
- Keep the prose formally written throughout; avoid colloquial transitions, casual hedges, and spoken-style fillers.

## Depth Control

Adjust depth to the request without dropping rigor:

- For "summarize this paper", keep background concise but still provide detailed method, setup, and result analysis.
- For "explain the core innovation", compress background and experiments, then expand method differentiation and why the idea helps.
- For "analyze the method section", expand architecture, equations, objectives, and training details.
- For "summarize experiments and ablations", expand setup, results, fairness caveats, what the ablations do or do not prove, and the necessary supporting visualizations.
- For "generate research insights", add stronger discussion of hidden assumptions, transferability, and promising extensions.

## Domain Routing

Use [references/domain-cues.md](references/domain-cues.md) when the paper falls into one or more of these areas:

- deep learning
- computer vision
- multimodal large models
- vision-language models
- object detection
- segmentation
- video understanding
- domain adaptation
- transformer-based architectures
- generative models

Use the domain cues to decide which architectural details, failure modes, and evaluation assumptions deserve extra scrutiny.

## Output Contract

Unless the user asks for a smaller format, include these sections:

- Paper Information
- Keywords
- Research Background
- Core Problem
- Main Contributions
- Method Overview
- Architecture And Pipeline
- Technical Details
- Experimental Setup
- Experimental Results
- Ablation Studies
- Strengths
- Weaknesses
- Limitations
- Possible Improvements
- Future Research Directions
- Related Work And References
- One-Sentence Summary

Translate the section titles into `output_language`, but keep the section order stable across languages.

Integrate loss functions and optimization into `Experimental Setup` instead of creating a separate `Loss Functions And Optimization` section.

Within `Related Work And References`, keep the related-work analysis as prose or bullets, then end with a simple numbered reference list in normal citation style.

If a section is unsupported by the available evidence, keep the heading and mark the content as unavailable or underspecified instead of hallucinating.
