---
title: "When Load-Balancing Goes Too Far: Expert Pruning in Over-Dispersed Mixture-of-Experts Models"
date: 2026-09-03
authors: ["Berkcan Kapusuzoglu", "Connor Pryor", "Sangwoo Cho", "Supriyo Chakraborty", "Shi-Xiong Zhang", "Sambit Sahu", "Milind Naphade"]
venue: {name: "NeurIPS 2026 Workshop on On-Device Intelligence", type: workshop}
status: accepted
links:
  - {label: "Read the arXiv preprint", url: "https://arxiv.org/abs/2609.04453"}
topics: ["mixture-of-experts", "pruning", "efficient inference"]
featured: true
featured_weight: 2
summary: "When load balancing spreads routing too uniformly across experts, router scores become less useful for deciding which experts to prune. Domain-aware score allocation accounts for which capabilities each expert supports."
contribution: "The paper characterizes expert pruning under over-dispersed routing and proposes Minimax Expert Score Allocation (MESA) to limit worst-case degradation across domains."
visuals:
  - id: ppl-accuracy
    file: media/ppl-accuracy.png
    role: lead
    alt: "Three scatter plots compare WikiText-2 perplexity with GSM8K, MMLU and GPQA-Diamond accuracy across five pruning methods at r = 0.25; correlations are positive or near zero."
    caption: "Perplexity does not reliably predict task accuracy across pruning configurations under over-dispersed routing. The comparison covers five methods at r = 0.25 on GSM8K, MMLU and GPQA-Diamond."
    takeaway: "Check the tasks you need to preserve: lower WikiText-2 perplexity does not consistently identify the more accurate pruning method in this comparison."
    source_label: "Berkcan Kapusuzoglu et al., When Load-Balancing Goes Too Far (2026), Figure 2"
    source_url: "https://arxiv.org/abs/2609.04453v1"
    license: "CC BY 4.0; rasterized without scientific edits"
---
