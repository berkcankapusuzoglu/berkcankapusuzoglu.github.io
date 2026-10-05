---
title: "Physics-Informed Machine Learning (PIML): Application to Additive Manufacturing"
date: 2022-04-19
description: "Three ways to combine physics knowledge, simulation data, and experimental measurements for additive-manufacturing prediction."
summary: "Physics-informed machine learning can make limited experimental data more useful by adding physical constraints, simulation outputs, or simulation-based pretraining."
original_url: "https://medium.com/@berkcan1992/physics-informed-machine-learning-piml-application-to-additive-manufacturing-3ddd2324059a"
---

*Originally published on Medium in 2022. This archive edition summarizes the central ideas. [Read the original on Medium](https://medium.com/@berkcan1992/physics-informed-machine-learning-piml-application-to-additive-manufacturing-3ddd2324059a).*

## Why bring physics into machine learning?

Physics-based models encode mechanisms we already understand, but they can be expensive or incomplete. Data-driven models can learn complex relationships, but manufacturing experiments are costly and the available dataset may be small. Physics-informed machine learning combines these information sources instead of treating them as competing choices.

The application in this work is fused filament fabrication. The prediction problem connects process settings with part-quality outcomes such as bond quality and porosity. A useful model must learn from experiments while respecting the structure supplied by manufacturing physics and simulation.

## Three integration strategies

The study compares three practical ways to add physics knowledge to a learning pipeline:

1. **Add physical constraints to the loss.** Training penalizes predictions that conflict with known relationships. This approach makes physics part of the learning objective.
2. **Use physics-model outputs as features.** Simulation results become additional model inputs alongside experimental variables. The learner can use both measured evidence and modeled structure.
3. **Pretrain with simulation, then update with experiments.** Simulation data provides an initial representation. Experimental observations then adapt the model toward the real process.

These strategies differ in where physics enters the pipeline. That distinction matters because the best choice depends on simulation fidelity, experimental coverage, and the kind of physical knowledge available.

## Practical takeaway

Physics information is most useful when its role is explicit and testable. Compare the hybrid model with both a data-only baseline and the underlying physics model. Evaluate not only average accuracy, but also behavior in regions with sparse experimental coverage. A hybrid method should earn its complexity by improving prediction where data alone is weakest.

## Related research

The full study appears in [*Physics-informed and hybrid machine learning in additive manufacturing: application to fused filament fabrication*](/publications/2020_kapusuzoglu_jom.html), published in the Journal of Metals. The [publisher record](https://link.springer.com/article/10.1007/s11837-020-04438-4) contains the complete paper.
