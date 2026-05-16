# Output Language

Use this file whenever the skill will generate a report, explanation, method analysis, experiment summary, citation analysis, strengths/weaknesses section, research insights, or future directions.

This file is the canonical source of truth for output-language policy in the final analytical report. Other skill files may summarize this policy briefly, but they should not redefine it in detail.

## First-class parameter

Treat `output_language` as a first-class input parameter.

- If the user explicitly requests a language, use it.
- If the user does not specify a language, default to the user's primary language.
- Common examples include Chinese, English, Japanese, Korean, and other major languages explicitly requested by the user.

## Core rules

The generated output must:

- produce the full report in `output_language`
- preserve technical terminology accuracy
- preserve original paper titles, citations, model names, dataset names, benchmark names, and author names
- translate explanations and analysis into the target language
- maintain consistent markdown structure across languages
- avoid mixed-language outputs

English technical terms may remain untranslated when that is the natural or accuracy-preserving choice in the target language.

## Consistency scope

Language consistency applies to:

- section titles
- technical analysis
- experiment summaries
- strengths and weaknesses
- research insights
- citation analysis
- future directions

Do not alternate between languages across sections. If the report is in Chinese, Japanese, Korean, or another requested language, keep the prose in that language throughout, except for protected source terms and conventional English technical terms.

## What to preserve verbatim

Preserve these in original form unless the user explicitly asks otherwise:

- paper titles
- citation keys or reference strings
- author names
- model names
- dataset and benchmark names
- code identifiers and metric abbreviations

Examples:

- keep `CLIP`, `GPT-4o`, `ImageNet`, `COCO`, `mAP`, `IoU`, and author names unchanged
- keep paper titles in original language/script
- translate the surrounding explanation into `output_language`

For equations, preserve the mathematical meaning and symbol choices from the paper, but follow [math-markdown.md](math-markdown.md) for the actual rendering and normalization rules.

## Markdown structure

Keep the same logical section order across languages. Translate the headings, not the structure.

For example, the canonical order is still:

1. Paper Information
2. Keywords
3. Research Background
4. Core Problem
5. Main Contributions
6. Method Overview
7. Technical Details
8. Architecture And Pipeline
9. Experimental Setup
10. Experimental Results
11. Ablation Studies
12. Strengths
13. Weaknesses
14. Limitations
15. Possible Improvements
16. Future Research Directions
17. Related Work And References
18. One-Sentence Summary

Only the heading text changes with `output_language`; the section ordering should remain stable unless the user explicitly asks for a different format.

## Translation guidance

- Translate explanations, summaries, and evaluative statements.
- Prefer terminology that researchers in the target language would actually use.
- Leave specialized English terms unchanged when translation would be awkward, ambiguous, or less standard.
- Do not over-translate citation strings or reference entries in ways that distort the original source information.
- Do not translate variable names, operator names, or equation content inside math spans unless the paper itself does so.

## PDF extraction boundary

This language policy applies to generated analytical output.

For `scripts/extract_pdf_figures.py`, the extracted markdown normally preserves source-document text and captions. If the user also wants a translated report, run extraction first and then generate the analytical report in `output_language`.
