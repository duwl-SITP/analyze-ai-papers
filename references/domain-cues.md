# Domain Cues

Use this file when the paper is in one of the target domains and the default rubric needs domain-specific emphasis.

## Contents

- General deep learning and computer vision
- Multimodal models and vision-language models
- Object detection
- Segmentation
- Video understanding
- Domain adaptation
- Transformer-based architectures
- Generative models

## General deep learning and computer vision

Inspect these recurring sources of improvement:

- stronger pretraining or larger backbones
- data curation and augmentation
- multi-scale training or higher resolution
- additional supervision signals
- inference heuristics that are easy to miss in the abstract

Ask whether the paper's claimed conceptual gain survives after controlling for recipe changes.

## Multimodal models and vision-language models

Focus on:

- modality encoders and whether they are frozen or trainable
- alignment mechanism: contrastive, cross-attention, generative decoding, retrieval, or instruction tuning
- grounding path between visual tokens, text tokens, and region or frame representations
- training data mixture, curation, and filtering
- hallucination, faithfulness, and grounding evaluation

Common hidden variable: the data mixture and instruction-tuning recipe matter as much as the architecture.

## Object detection

Inspect:

- detector family: anchor-based, anchor-free, query-based, two-stage, one-stage
- label assignment or matching strategy
- box regression parameterization
- multi-scale features, neck design, and query count
- NMS, score calibration, or other post-processing
- class imbalance handling and long-tail effects

Ask whether gains are localization gains, classification gains, or mostly post-processing gains.

## Segmentation

Inspect:

- semantic, instance, panoptic, video, or promptable segmentation setting
- mask representation and decoder design
- query-to-mask or pixel-to-mask mapping
- boundary quality and high-resolution processing
- mask loss composition and matching strategy
- prompt or interactive conditioning if present

Ask whether gains come from better mask decoding, stronger features, or heavier supervision.

## Video understanding

Inspect:

- clip sampling strategy and temporal window
- temporal aggregation: attention, memory, recurrence, pooling, or tubelets
- causal versus offline setting
- frame-level versus clip-level objectives
- compute and latency as sequence length grows
- pretraining source, especially image-only versus video pretraining

Ask whether the method genuinely models time or mainly inherits stronger spatial features.

## Domain adaptation

Inspect:

- source and target supervision levels
- where adaptation happens: pixel space, feature space, output space, or self-training
- pseudo-label generation and filtering
- augmentation coupling between weak and strong views
- schedule for turning on unsupervised losses
- robustness to domain gap size

Ask whether gains come from better alignment, better pseudo-labels, better scheduling, or simply stronger augmentations and training tricks.

## Transformer-based architectures

Inspect:

- tokenization strategy and sequence length
- positional encoding or relative bias
- attention pattern: global, local, windowed, sparse, linearized, or hierarchical
- decoder queries, memory layout, and cross-attention interfaces
- scaling behavior with image, video, or multimodal resolution

Ask whether the contribution changes the transformer's inductive bias or mostly its training recipe.

## Generative models

Inspect:

- objective family: autoregressive, diffusion, flow, GAN, masked modeling, or hybrid
- conditioning path: text, class, layout, image, video, or retrieval context
- sampling procedure and inference-time guidance
- tradeoff among fidelity, diversity, controllability, and speed
- evaluation reliability: FID-like metrics, human study, downstream utility, or prompt suite design

Ask whether gains come from the model architecture, the sampler, the guidance strategy, or data scale.
