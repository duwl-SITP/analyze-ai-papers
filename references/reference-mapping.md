# Reference Mapping

Use this file when the user asks for related work, cited-paper summaries, foundational references, or differences from prior work.

## Prioritize references

Prioritize references that appear in one or more of these places:

- the introduction as direct predecessors
- the related-work section as nearest alternatives
- result tables as named baselines
- the method section as borrowed architecture or loss components
- repeated discussion across multiple sections

Treat dataset, benchmark, or metric papers as secondary unless the evaluation protocol itself is part of the paper's contribution.

## Classify each important reference

Use one of these roles for each cited paper:

- Foundational work
- Closest prior work
- Baseline family
- Borrowed component
- Training or data recipe precedent
- Benchmark or protocol reference

If a citation plays multiple roles, say which role matters most for understanding the current paper.

## Explain the role, not just the title

For each important cited paper, explain:

- why the current paper cites it
- which idea, architecture, loss, or setup it contributes to the story
- whether the current paper extends it, replaces it, simplifies it, or competes with it

## Stay within the evidence boundary

If the cited paper itself is not provided, summarize its role from the current paper's citation context rather than pretending to have fully read it.

Useful phrasing:

- "Based on how this paper cites it, ..."
- "The current paper treats this as a foundational baseline for ..."
- "The exact internals of the cited work are not available here, but its role in the comparison is ..."

## Output pattern

Use a compact table when the user asks for related work or references:

| Reference | Role | Why It Matters Here | How The Current Paper Differs | Confidence |
| --- | --- | --- | --- | --- |
| [Paper or citation key] | [Foundational / closest prior / baseline] | [One sentence] | [One sentence] | [Direct / inferred] |

Then add two short subsections:

## Foundational Works

- List the references that define the task, architecture family, or evaluation setup.

## Closest Prior Works

- List the works the current paper most directly builds on or competes against.
- State the most meaningful technical difference, not just the benchmark gap.

## What to avoid

- Do not list every citation unless the user explicitly asks for exhaustive coverage.
- Do not overstate novelty based only on citation absence.
- Do not claim detailed knowledge of a cited paper that is unavailable in the current evidence.
