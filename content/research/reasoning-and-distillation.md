---
title: "Reasoning and Distillation"
date: 2026-09-29
description: "Training language models to improve their reasoning by learning from critiques and refinement."
---

## The problem

Language models can produce plausible answers that contain reasoning mistakes. A useful training method should help a smaller model learn to revise such answers without requiring an extra critique-generation step every time it runs.

## The work

In [Critique-Guided Distillation for Robust Reasoning via Refinement](../publications/2026-critique-guided-distillation.html), we use teacher critiques as supervision during training. The student learns to refine flawed responses, while critique generation stays out of the inference path. The paper reports this as a training framework for improving response refinement.

## Why it matters

Separating training supervision from inference can make a reasoning method easier to use in systems where each additional model call matters. The paper describes one concrete way to teach refinement while keeping the runtime interaction focused on the answer.
