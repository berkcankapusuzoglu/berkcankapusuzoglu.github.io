---
title: "Efficient Model Systems"
date: 2026-09-03
description: "Methods for improving model efficiency through expert selection and careful adaptation."
---

## The problem

Large models often divide computation among specialized components. In mixture-of-experts models, routing and load balancing affect which experts are used; when routing is over-dispersed, common importance signals can become less reliable for deciding what to keep.

## The work

In [When Load-Balancing Goes Too Far: Expert Pruning in Over-Dispersed Mixture-of-Experts Models](../publications/2026-load-balancing-expert-pruning.html), we study pruning under over-dispersed routing and introduce Minimax Expert Score Allocation (MESA), a domain-aware way to allocate expert scores while limiting worst-case degradation across domains. The [SPEAR-MM paper](../publications/2025-spear-mm.html) studies a different efficiency problem: adapting a language model to a domain while restoring parameters to retain general capabilities.

## Why it matters

Efficiency depends on how a model is selected, adapted, and assessed. These papers examine complementary parts of that process, from choosing experts to evaluating and restoring parameters during adaptation.
