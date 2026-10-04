---
title: "SPEAR-MM: Selective Parameter Evaluation and Restoration via Model Merging for Efficient Financial LLM Adaptation"
date: 2025-11-11
authors: ["Berkcan Kapusuzoglu", "Supriyo Chakraborty", "Renkun Ni", "Stephen Rawls", "Sambit Sahu"]
venue: {name: "2025 IEEE International Conference on Big Data", type: conference}
status: published
links:
  - {label: "IEEE Big Data 2025 paper", url: "https://doi.org/10.1109/BigData66926.2025.11402347"}
topics: ["model merging", "financial language models", "efficient adaptation"]
featured: true
featured_weight: 3
summary: "SPEAR-MM uses post-hoc layer evaluation and spherical interpolation merging to preserve general capabilities during financial-domain adaptation of language models."
contribution: "The work presents a selective evaluation and restoration framework for balancing domain adaptation with retention of general capabilities."
visuals:
  - id: spear-pipeline
    file: media/spear-pipeline.png
    role: lead
    alt: "Five-step SPEAR-MM pipeline: financial fine-tuning, layer scoring, parameter ranking, merge configuration and validation of the merged model."
    caption: "SPEAR-MM evaluates layer importance and selectively restores parameters through spherical merging. Scores combine signal-to-noise and parameter-change metrics from the base and adapted models."
    takeaway: "Evaluate which layers changed, then choose what to restore from the base model and validate the merged configuration."
    source_label: "Berkcan Kapusuzoglu et al., SPEAR-MM (2025), Figure 1"
    source_url: "https://arxiv.org/abs/2511.08500v1"
    license: "CC BY 4.0; rasterized without scientific edits"
  - id: retention-adaptation
    file: media/retention-adaptation.png
    role: result
    alt: "Scatter plot of general knowledge retention and domain performance: three SPEAR-MM freezing configurations trace a trade-off alongside Baseline A and Baseline B."
    caption: "Domain adaptation and retention of general capabilities form a controllable trade-off. Each SPEAR-MM point represents a different freezing configuration; the y-axis reports domain performance relative to the non-adapted baseline."
    takeaway: "Choose a configuration for the balance you need: the reported SPEAR-MM settings offer a stronger adaptation-retention trade-off than Baseline A and Baseline B in this evaluation."
    source_label: "Berkcan Kapusuzoglu et al., SPEAR-MM (2025), Figure 2"
    source_url: "https://arxiv.org/abs/2511.08500v1"
    license: "CC BY 4.0; rasterized without scientific edits"
---
