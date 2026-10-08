---
title: "Critique-Guided Distillation for Robust Reasoning via Refinement"
date: 2026-09-29
authors: ["Berkcan Kapusuzoglu", "Supriyo Chakraborty", "Zain Sarwar", "Chia-Hsuan Lee", "Sambit Sahu"]
venue: {name: "International Conference on Machine Learning (ICML 2026)", type: proceedings}
status: published
links:
  - {label: "PMLR proceedings paper", url: "https://proceedings.mlr.press/v306/kapusuzoglu26a.html"}
topics: ["reasoning", "distillation", "language models"]
featured: true
featured_weight: 1
summary: "Critique-Guided Distillation trains a student to refine flawed responses using teacher critiques as training-only supervision, without requiring critiques at inference."
contribution: "The work introduces a training framework that separates critique consumption during fine-tuning from critique generation at inference."
visuals:
  - id: cgd-overview
    file: media/cgd-overview.png
    role: lead
    homepage: true
    alt: "CGD training workflow: the student drafts an answer, the teacher critiques and refines it, and the student learns the refined answer."
    caption: "A student learns from teacher critiques and refined answers during training, then answers without a teacher at inference."
    takeaway: "Teach the student to act on feedback during training so it can answer in one pass at inference."
    source_label: "Berkcan Kapusuzoglu et al., Critique-Guided Distillation (2026), Figure 1"
    source_url: "https://arxiv.org/abs/2505.11628v4"
    license: "CC BY 4.0; rasterized without scientific edits"
  - id: cgd-accuracy
    file: media/cgd-accuracy.png
    role: result
    alt: "Bar chart comparing the base model and four training methods across six reasoning evaluations for a LLaMA3.1-8B Instruct student; hatched CGD bars exceed distilled SFT and CFT bars."
    caption: "CGD improves LLaMA3.1-8B reasoning performance compared with distilled SFT and critique fine-tuning. The experiment uses a LLaMA3.3-70B Instruct teacher and 100K WebInstruct samples."
    takeaway: "In this experiment, learning to use critiques improves accuracy beyond learning refined answers alone or learning to generate critiques."
    source_label: "Berkcan Kapusuzoglu et al., Critique-Guided Distillation (2026), Figure 2"
    source_url: "https://arxiv.org/abs/2505.11628v4"
    license: "CC BY 4.0; rasterized without scientific edits"
---
