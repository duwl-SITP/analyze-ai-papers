---
name: analyze-ai-papers
description: Read, analyze, and summarize AI research papers with emphasis on deep learning, computer vision, multimodal models, vision-language models, object detection, segmentation, video understanding, domain adaptation, transformer architectures, and generative models. Use when Codex needs to turn a paper PDF, excerpt, arXiv text, figure description, or method/experiment section into a technically rigorous analysis of motivation, contributions, architecture, equations, losses, training strategy, experiments, ablations, limitations, related work, or future research directions.
---

# Analyze AI Papers

Use this skill to produce evidence-grounded technical analysis of research papers. Default to a structured markdown report and shorten only when the user explicitly asks for a brief answer.

## Quick Start

1. Read the actual paper content before summarizing. Prefer the PDF, extracted text, appendix, supplemental material, or provided excerpts over metadata-only summaries.
2. State the evidence boundary up front when the input is incomplete. If only the title, abstract, or a partial section is available, say so and avoid inventing missing details.
3. Read [references/analysis-rubric.md](references/analysis-rubric.md) for the full analysis checklist.
4. Read [references/domain-cues.md](references/domain-cues.md) when the paper is in vision, multimodal modeling, detection, segmentation, video, domain adaptation, transformer architectures, or generative modeling.
5. Read [references/reference-mapping.md](references/reference-mapping.md) when the user asks about related work, references, foundational papers, or differences from prior work.
6. Use [assets/templates/full-paper-analysis.md](assets/templates/full-paper-analysis.md) as the default report skeleton. Use the narrower templates only when the user asks for an experiments-only or references-only output.

## Workflow

### 1. Establish the evidence boundary

- Identify what is actually available: full paper, appendix, supplemental, figures, tables, only title/abstract, or user excerpts.
- Say explicitly which parts were read.
- Treat missing details as unknown. Do not backfill them with likely-but-unverified claims.

### 2. Parse the paper structure

Extract the paper into the closest available versions of these units:

- Title, authors, venue/year if present
- Abstract
- Introduction
- Related work
- Method or approach
- Architecture or pipeline figures
- Loss, objective, or optimization sections
- Experimental setup
- Main results
- Ablations or analysis
- Limitations or conclusion
- Appendix or supplemental details

If the paper uses unusual section names, map them to these functional roles instead of preserving superficial headings.

### 3. Identify the research problem and motivation

- State the target task and input/output setting precisely.
- Explain what gap in prior work the authors claim to address.
- Distinguish problem-level novelty from implementation-level improvement.
- Note whether the motivation is driven by accuracy, efficiency, robustness, generalization, data scarcity, cross-domain transfer, multimodal grounding, or generation quality.

### 4. Analyze the technical method

- Summarize the method at two levels:
  - a 3-5 sentence overview of the end-to-end pipeline
  - a component-level explanation of the architecture
- Name the modules, information flow, representations, and supervision signals.
- Explain why each major component exists, not just what it is called.
- Identify whether gains plausibly come from architecture, objective design, optimization, data engineering, pretraining, or inference-time heuristics.

### 5. Interpret equations and objectives

- Rewrite key equations in plain language.
- Define each loss term, constraint, regularizer, matching objective, or generative objective.
- Explain how the objective couples with the architecture and data pipeline.
- Call out training schedules, teacher-student updates, EMA, warmup, burn-in, multi-stage optimization, pseudo-labeling, retrieval steps, or auxiliary objectives.
- If the paper omits needed definitions, say what is underspecified.

### 6. Analyze experiments and ablations

- Record datasets, splits, metrics, baselines, and compute regime.
- Separate main benchmark results from controlled ablations.
- Identify what each ablation actually isolates.
- Note whether improvements are broad or narrow: only on one dataset, only at large scale, only with extra data, only under a specific metric, or only with strong pretraining.
- Flag comparisons that may be unfair because of data, compute, resolution, pretraining, tuning budget, or implementation differences.

### 7. Evaluate strengths, weaknesses, and limitations

- Be concrete and tie each point to evidence from the paper.
- Discuss computational complexity, memory cost, inference latency, annotation burden, extra modules, dependence on pretraining, sensitivity to hyperparameters, and generalization assumptions.
- Prefer falsifiable observations over generic praise or criticism.

### 8. Analyze related work and references

- Prioritize cited papers that are foundational, closest prior work, or direct baselines.
- Explain the role each reference plays in the argument: problem framing, architecture lineage, loss design, benchmark protocol, or comparison target.
- State how the current paper differs from the closest prior works.

### 9. Generate research insights

- Extract what is reusable beyond the paper's headline result.
- Suggest plausible follow-up directions grounded in the method's actual bottlenecks.
- Separate paper claims from your own inference.

### 10. Write the output

- Use the report template headings unless the user requests a different format.
- Keep terminology precise and implementation-oriented.
- Prefer short, dense paragraphs or compact bullets over vague summaries.
- End with a one-sentence summary that captures problem, method, and main takeaway.

## Reporting Rules

- Attribute claims carefully:
  - "The paper claims..." for author assertions.
  - "The experiments show..." for reported evidence.
  - "A likely reason is..." for your inference.
- Do not call a result stronger than the evidence supports.
- Do not infer novelty from branding or naming alone.
- Do not treat ablations as proof of mechanism unless the ablation isolates that mechanism.
- Prefer exact terminology from the paper, but translate jargon when it blocks understanding.
- When numbers, equations, or training details matter, quote them precisely or paraphrase them faithfully from the source.
- If a figure is central to the method, describe the data flow in words.

## Depth Control

Adjust depth to the request without dropping rigor:

- For "summarize this paper", produce the default structured report but keep each section concise.
- For "explain the core innovation", compress background and experiments, then expand method differentiation and why the idea helps.
- For "analyze the method section", expand architecture, equations, objectives, and training details.
- For "summarize experiments and ablations", expand setup, results, fairness caveats, and what the ablations do or do not prove.
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
- Technical Details
- Architecture And Pipeline
- Loss Functions And Optimization
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

If a section is unsupported by the available evidence, keep the heading and mark the content as unavailable or underspecified instead of hallucinating.
