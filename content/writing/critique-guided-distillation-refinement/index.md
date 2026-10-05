---
title: "Learning from mistakes with critique-guided distillation"
date: 2026-10-04
description: "How training-only teacher feedback helps a student refine its reasoning, and what the reported accuracy gains establish."
summary: "Teacher feedback can supervise refinement during training while the deployed student answers from the prompt alone. A visual guide to CGD and its evaluation limits."
linkedin:
  thesis: "Teach a reasoning model to act on feedback during training, then evaluate whether that behavior transfers to prompt-only inference."
  takeaways:
    - "Student mistakes can reveal what a correct teacher answer leaves implicit."
    - "Critique consumption and critique generation are different training objectives."
    - "Removing the teacher from inference does not remove the need to measure token cost and capability retention."
  sharing: "Adapt the thesis and a takeaway into a LinkedIn post that links to this canonical note. Do not reproduce the full article."
visuals:
  - id: cgd-training-sequence
    file: media/cgd-overview.png
    role: lead
    exact_pixels: true
    alt: "Three-row CGD training diagram showing the student response, teacher critique and refined answer, and student fine-tuning."
    caption: "Figure 1 contains three training rows. The sequence highlights the initial response, teacher feedback, and refinement target. The final view keeps the full diagram and explains prompt-only inference separately."
    takeaway: "Use teacher critiques as training context; deploy the student with the prompt alone."
    source_label: "Kapusuzoglu et al. (2026), Figure 1 and Section 3"
    source_url: "https://arxiv.org/abs/2505.11628v4"
    license: "CC BY 4.0; exact source pixels with separate CSS focus outlines"
    sequence:
      - file: media/cgd-overview.png
        label: "Initial student response"
        duration: 3000
        focus: {x: 1.5, "y": 1.5, width: 98, height: 26.5}
      - file: media/cgd-overview.png
        label: "Teacher critique"
        duration: 3000
        focus: {x: 60.5, "y": 34.5, width: 39, height: 23.5}
      - file: media/cgd-overview.png
        label: "Refined answer and student training"
        duration: 3000
        focus: {x: 1.5, "y": 60.5, width: 98, height: 38}
      - file: media/cgd-overview.png
        label: "Teacher-free inference"
        duration: 3000
        callout: "Prompt only. No teacher or critique at inference. This is the deployment behavior described in Section 3.2, not a fourth row in Figure 1."
  - id: cgd-accuracy
    file: media/cgd-accuracy.png
    role: result
    alt: "Bar chart comparing the base model and four training methods across six reasoning evaluations for a LLaMA3.1-8B Instruct student; CGD exceeds distilled SFT and critique fine-tuning."
    caption: "Figure 2 compares methods for LLaMA3.1-8B Instruct using a LLaMA3.3-70B Instruct teacher and 100K WebInstruct samples. The comparisons shown are specific to this setup."
    takeaway: "CGD improves accuracy over distilled SFT and critique fine-tuning in this experiment."
    source_label: "Kapusuzoglu et al. (2026), Figure 2"
    source_url: "https://arxiv.org/abs/2505.11628v4"
    license: "CC BY 4.0; rasterized without scientific edits"
---

## What a correct answer leaves out

When a student makes the same reasoning mistake repeatedly, a correct teacher answer may not explain which assumption needs to change. Distillation can pass along the destination while leaving that repair implicit. For an engineer designing training data, the useful question is whether feedback tied to the student's own attempt can supply a better learning signal.

## Critique as training context

[Critique-Guided Distillation (CGD)](https://arxiv.org/html/2505.11628v4#S3) conditions supervised training on a prompt, a student attempt, and teacher feedback, with the teacher's refined answer as the target. The student learns to use feedback. At deployment, it receives only the prompt.

## Follow the sequence

1. Generate an initial student response to expose its errors.
2. Ask the teacher for a critique of that response.
3. Generate a refined teacher answer and train the student to produce it from the augmented context.
4. Evaluate the trained student with prompts alone. No teacher call is added at inference.

The outline changes emphasis without altering the diagram. The complete figure remains available at every step.

{{< research-visual >}}

## Read the result at the right scope

[Figure 2](https://arxiv.org/html/2505.11628v4#S1.F2) supports a comparison of CGD with distilled SFT and critique fine-tuning for the pictured student, teacher, data, and benchmarks. It does not establish reliability on arbitrary tasks or a causal explanation of every gain.

{{< research-visual >}}

## What to measure before adopting it

For a new application, compare prompt-only accuracy with answer distillation under matched data and training budgets. Inspect whether feedback identifies a specific error and whether the refined answer actually repairs it. Track instruction following and failures beyond the training domain, alongside response length and latency.

The paper's [limitations](https://arxiv.org/html/2505.11628v4#S5) include dependence on informative teacher feedback, data generation cost, and evaluation focused on structured reasoning. A teacher-free inference path avoids extra critique calls; it does not guarantee shorter responses or lower end-to-end cost.

The practical lesson is to make the repair signal explicit during training and test its transfer to the deployment input. Treat that transfer as an evaluation question each time the student, teacher, or task changes.

## Paper and citation

Berkcan Kapusuzoglu, Supriyo Chakraborty, Zain Sarwar, Chia-Hsuan Lee, and Sambit Sahu. *Critique-Guided Distillation for Robust Reasoning via Refinement.* Proceedings of the 43rd International Conference on Machine Learning, PMLR 306, 2026. [Proceedings record](https://proceedings.mlr.press/v306/kapusuzoglu26a.html). [Public manuscript, version 4](https://arxiv.org/abs/2505.11628v4). [Publication page](/publications/2026-critique-guided-distillation.html).
