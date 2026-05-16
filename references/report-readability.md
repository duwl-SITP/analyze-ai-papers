# Report Readability

Use this file to keep the final analysis report technically dense but easy to follow. The priority is paragraph-level semantic continuity: each sentence should make clear how the next concept follows from the previous one.

This file is the canonical source of truth for paragraph-level readability, concept transitions, and formula framing in the final analytical report. Other skill files may mention these expectations briefly, but they should not restate them in full.

## Paragraph-Level Continuity

When introducing a new concept, first answer three questions:

- Where does it come from in the paper's method, data flow, training setup, or objective?
- Why does it appear at this point in the explanation?
- How does it relate to the object discussed in the previous sentence?

Do not let a new prompt, module, loss, variable, constraint, representation, or training target appear as if it were already established. If a paragraph moves from concept A to concept B, add a bridge sentence explaining why B is the next step for solving A.

## Preferred Sentence Order

Within a technical paragraph, prefer this order:

1. Existing object or problem.
2. Source of the new object.
3. Relationship between the new object and the existing object.
4. How the method uses the new object.
5. Intended result, constraint, or downstream effect.

This order is especially important in `Technical Details`, `Architecture And Pipeline`, and `Experimental Setup`, where dense method descriptions often introduce representations, prompts, losses, and constraints close together.

## Abrupt Concept Jumps To Avoid

- Do not jump from input decomposition directly to a prompt constraint unless the text first explains how the prompt acts on the input, feature representation, causal part, or spurious part.
- Do not introduce a loss immediately after a module name unless the text explains what behavior the module needs to be trained to produce.
- Do not introduce a variable or symbol in a formula before explaining what paper object it denotes.
- Do not introduce a constraint before explaining which failure mode or degree of freedom makes the constraint necessary.
- Do not move from architecture to training objective without explaining which representation or prediction the objective supervises.

## Formulas And Constraints

Before a formula, explain the local motivation: what method step, invariance claim, optimization need, or failure mode requires this expression.

After a formula, explain its role: what it constrains, optimizes, measures, regularizes, or couples with the architecture.

Avoid phrases like "the paper gives the following condition" when the previous sentence has not explained why that condition is needed. Prefer a bridge that connects the condition to the preceding representation, prompt, module, or objective.

## Language-Aware Writing

Apply these rules in every `output_language`. In Chinese reports, avoid English-style compressed technical fragments that place nouns side by side without logical connectors. Use explicit relation words such as "在此基础上", "因此", "为了约束", "这一信号作用于", and "它与前述表示的关系是" when they clarify the method chain.

## Minimal Example Pattern

If a paper decomposes an input representation into causal and spurious parts and then introduces a prompt, the paragraph should connect the steps:

- The input decomposition separates the stable task-relevant structure from domain-specific or spurious factors.
- The prompt is then introduced as a learnable perturbation or conditioning signal that acts on this representation.
- Because the prompt can expose whether the representation depends on non-causal factors, the method constrains its effect differently on the causal and spurious parts.
- This motivates the invariance condition or training objective that follows.

The wording can vary, but the logical chain must be explicit: input decomposition -> prompt source and role -> how the prompt acts on the decomposition -> why the next condition or objective is needed.
