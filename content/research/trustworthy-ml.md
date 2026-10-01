---
title: "Trustworthy Evaluation"
date: 2025-11-11
description: "Evaluation practices that make reasoning and model adaptation easier to assess."
---

## The problem

Model changes can improve one task while weakening behavior elsewhere. Reliable conclusions depend on measuring the intended capability and checking what a change preserves.

## The work

[SPEAR-MM](../publications/2025-spear-mm.html) evaluates model layers after domain adaptation and uses parameter restoration through model merging to preserve general capabilities. In [Critique-Guided Distillation](../publications/2026-critique-guided-distillation.html), the training setup separates critique supervision from inference, making the source of refinement behavior explicit.

## Why it matters

Evaluation is part of system design. These papers make specific choices about what to measure and when: capability retention after adaptation, and response refinement learned from training-time critiques.
