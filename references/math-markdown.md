# Math Markdown

Use this file whenever the skill will generate a final analytical report that contains equations, symbols, losses, scoring rules, or variable names from a paper.

This file is the canonical source of truth for math formatting in the final analytical report. Other skill files may mention math formatting briefly, but they should not restate these rules in full.

The goal is stable markdown math rendering in the final saved report. Preserve the paper's mathematical meaning, but normalize the notation into consistent markdown math syntax.

## Core rules

- Use `$...$` for inline math.
- Use `$$...$$` for standalone display equations.
- Never emit raw LaTeX fragments outside math delimiters.
- Never leave TeX commands, superscripts, subscripts, or arrow expressions as plain prose.
- Prefer one contiguous math span for one contiguous mathematical expression.
- Keep natural-language explanation outside math delimiters unless a short text label must appear inside the equation.

## Required normalization

If a symbol or expression is mathematical, wrap it in math delimiters even if the source PDF or OCR text exposed it as plain text.

Apply this to:

- TeX commands such as `\mathcal`, `\mathbf`, `\Sigma`, `\delta`, `\lambda`, `\log`, `\exp`
- superscripts and subscripts such as `p^*`, `x_t`, `H_{\text{causal}}`
- function notation such as `f_C(x)`, `f_S(x)`, `g(z)`
- operators and arrows such as `\to`, `\mapsto`, `\approx`, `\leq`
- compact mathematical phrases such as `\Sigma_{c^\perp} \to 0`

## Good defaults

- Preserve the equation content, but normalize the wrapper syntax to markdown math.
- Use `\text{...}` only inside math when you need a short label like `\text{causal}`.
- Do not wrap an entire explanatory sentence in `$...$`.
- If a paragraph mixes prose and math, wrap only the mathematical spans.
- If an equation is central and multi-line in the source, prefer a short faithful display equation over a broken inline fragment.

## Examples

Wrong:

- `\mathcal{F}`
- `\mathcal{F}^{-1}`
- `\delta`
- `f_C(x)`
- `H_{\text{causal}} is the causal entropy term`
- `\Sigma_{c^\perp} \to 0`

Right:

- `$\mathcal{F}$`
- `$\mathcal{F}^{-1}$`
- `$\delta$`
- `$f_C(x)$`
- `$H_{\text{causal}}$ is the causal entropy term`
- `$\Sigma_{c^\perp} \to 0$`

Wrong:

- `The score is p^* after normalization.`
- `The paper computes \delta from the residual branch.`

Right:

- `The score is $p^*$ after normalization.`
- `The paper computes $\delta$ from the residual branch.`

## Final self-check

Before finalizing the report, scan it for bare math-like fragments and rewrite them into markdown math syntax.

Pay special attention to:

- unwrapped backslash commands
- unwrapped `_` and `^` patterns
- unwrapped `\text{...}` inside symbol names
- arrow expressions like `\to`
- isolated symbol phrases copied directly from the PDF
