# Reference Mapping

Use this file when the user asks for related work, cited-paper summaries, or differences from prior work.

## Prioritize references

Prioritize references that appear in one or more of these places:

- the introduction as direct predecessors
- the related-work section as nearest alternatives
- result tables as named baselines
- the method section as borrowed architecture or loss components
- repeated discussion across multiple sections

Treat dataset, benchmark, or metric papers as secondary unless the evaluation protocol itself is part of the paper's contribution.

## Explain the role, not just the title

For the most important cited papers, explain in normal prose or compact bullets:

- why the current paper cites them
- which idea, architecture, loss, or setup they contribute to the story
- whether the current paper extends them, replaces them, simplifies them, or competes with them

## Stay within the evidence boundary

If the cited paper itself is not provided, summarize its role from the current paper's citation context rather than pretending to have fully read it.

Useful phrasing:

- "Based on how this paper cites it, ..."
- "The current paper uses this as a comparison target for ..."
- "The exact internals of the cited work are not available here, but its role in the comparison is ..."

## Output pattern

Use a numbered reference list when the user asks for related work or references. Do not use a table.

Recommended pattern:

```markdown
## Related Work Positioning

- Main comparison axis:
- Most relevant prior methods discussed:
- How the current paper is positioned against them:

## References

[1] Author(s). Paper title. Venue or source, year.
[2] Author(s). Paper title. Venue or source, year.
```

If complete bibliographic metadata is unavailable, keep the cleanest citation string visible from the source paper and do not invent missing fields. Do not create separate “Foundational Works” or “Closest Prior Works” sections unless the user explicitly asks for them.

## What to avoid

- Do not list every citation unless the user explicitly asks for exhaustive coverage.
- Do not overstate novelty based only on citation absence.
- Do not claim detailed knowledge of a cited paper that is unavailable in the current evidence.
- Do not turn the references section into a metadata-heavy bibliography when the user only needs analytical positioning.
- Do not emit per-reference `Role`, `Why it matters`, or `Confidence` fields unless the user explicitly asks for that schema.
