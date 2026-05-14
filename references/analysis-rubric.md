# Analysis Rubric

Use this file as the detailed checklist behind the default report.

## Contents

- Evidence boundary
- Problem and motivation
- Contributions
- Method and architecture
- Objectives and optimization
- Training strategy
- Experimental setup
- Results and ablations
- Complexity and efficiency
- Strengths and weaknesses
- Limitations and future work
- Reporting checklist

## Evidence boundary

- Verify which artifacts are available: full paper, appendix, supplement, figures, tables, or partial excerpts.
- Prefer appendix and supplemental material when training details or ablations are missing from the main paper.
- Mark missing evidence explicitly instead of inferring absent details.

## Problem and motivation

- What task does the paper solve?
- What is the exact input/output formulation?
- What failure mode or bottleneck in prior work motivates the method?
- Is the motivation about accuracy, robustness, efficiency, data efficiency, transfer, grounding, or generation quality?

## Contributions

Separate contributions into categories rather than repeating the abstract:

- problem framing
- architecture
- objective or loss
- optimization or training recipe
- dataset or data curation
- evaluation protocol
- systems or efficiency engineering

Check whether the claimed contribution is central to the results or mostly packaging.

## Method and architecture

Explain the method from coarse to fine:

1. End-to-end pipeline
2. Main components and data flow
3. Representations and interfaces between modules
4. Training-only components versus inference-time components

Look for these failure-prone details:

- hidden dependence on pretraining
- extra teacher or memory branches used only during training
- post-processing or reranking that changes the final result
- extra data or pseudo-label pipelines outside the nominal model

## Objectives and optimization

For each important equation or training objective, answer:

- What is being optimized?
- What are the supervision sources?
- Which terms are primary versus auxiliary?
- Which terms operate on features, logits, boxes, masks, tokens, or generated outputs?
- How does the objective reinforce the architectural claim?

When the paper has several losses, identify whether the gain likely comes from:

- a new target signal
- a better weighting or schedule
- an easier optimization path
- stronger regularization
- richer data exposure

## Training strategy

Extract training details that materially affect reproducibility:

- optimizer and learning-rate schedule
- batch size and training length
- warmup, cooldown, EMA, gradient clipping
- staged training, curriculum, self-training, distillation, or burn-in periods
- data augmentation, prompt construction, negative sampling, or mining
- frozen versus trainable modules

If the paper says the method is simple but the recipe is elaborate, say that plainly.

## Experimental setup

Record the evaluation setting precisely:

- datasets and splits
- metrics
- baseline families
- pretraining sources
- input resolution or token budget
- compute regime if reported

Check for common comparability problems:

- stronger pretraining than baselines
- extra unlabeled or synthetic data
- test-time augmentation or ensembling
- different backbone scale or inference budget
- unpublished tuning differences

## Results and ablations

Read tables with two separate questions:

1. What is the headline empirical claim?
2. What evidence actually supports that claim?

For ablations, ask:

- What variable changed?
- Was only one factor changed?
- Does the ablation support the mechanism or only the end result?
- Are there missing controls that would materially change the conclusion?

When reporting results, state whether gains are:

- consistent across datasets
- concentrated in one metric
- stronger in large models than small ones
- dependent on scale, data, or compute

When the paper provides qualitative figures, error cases, retrieval examples, confusion visualizations, attention maps, or ablation plots that materially affect interpretation:

- include the necessary visualization in the report or refer to it explicitly
- explain what the visualization evidences
- distinguish illustrative qualitative evidence from stronger quantitative evidence

## Complexity and efficiency

Look beyond parameter count:

- FLOPs or attention complexity
- latency and memory footprint
- number of views, crops, sampling steps, or decode passes
- training stability cost
- external modules such as retrievers, detectors, segmenters, or teachers

If efficiency claims are missing supporting numbers, mark them as weakly supported.

## Strengths and weaknesses

Keep these grounded in evidence.

Strength examples:

- clean architectural idea with direct ablation support
- strong improvement under a fair comparison
- better robustness or transfer under matched compute
- clear simplification of an existing pipeline

Weakness examples:

- gains depend on extra data or stronger pretraining
- main effect may come from training recipe rather than architecture
- ablations do not isolate the claimed mechanism
- evaluation is narrow or benchmark-specific
- computational overhead is under-discussed

## Limitations and future work

Separate author-stated limitations from your own technical inference.

Prefer future directions that directly follow from the paper's bottlenecks:

- remove brittle heuristics
- reduce annotation or compute cost
- test broader generalization
- replace hand-tuned schedules with learned adaptation
- simplify multi-stage training

## Reporting checklist

Before finishing, check that the report:

- states the evidence boundary
- distinguishes paper claims from your inference
- explains why the method should work
- identifies likely sources of gain
- covers both experiments and ablations
- names important limitations
- avoids generic praise
