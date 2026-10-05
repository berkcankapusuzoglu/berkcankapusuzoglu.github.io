---
title: "Multi-objective Optimization Under Uncertainty"
date: 2022-04-13
description: "How Pareto trade-offs, predictive uncertainty, and robust design support process decisions with conflicting objectives."
summary: "Real design problems balance conflicting goals, and the best deterministic trade-off may be fragile once input and model uncertainty are included."
original_url: "https://medium.com/@berkcan1992/multi-objective-optimization-under-uncertainty-858592e662ce"
---

*Originally published on Medium in 2022. This archive edition summarizes the central ideas. [Read the original on Medium](https://medium.com/@berkcan1992/multi-objective-optimization-under-uncertainty-858592e662ce).*

## Why one objective is rarely enough

Engineering decisions often involve goals that cannot all be improved at once. A manufacturing process may need to improve geometric accuracy and bond quality while limiting cost or variability. Multi-objective optimization represents those conflicts directly instead of hiding them inside one performance score.

The result is usually a Pareto front. Each point represents a design for which improving one objective would worsen another. The front does not make the decision automatically. It exposes the available trade-offs so a decision-maker can choose among them.

## Deterministic optima can be fragile

A design that looks best at nominal inputs may perform poorly when operating conditions change. Prediction models also introduce uncertainty through limited data, uncertain parameters, measurement noise, and model error. Ignoring these sources can produce a precise-looking answer that is not reliable.

Bayesian neural networks offer one way to represent predictive uncertainty in a data-driven surrogate. Repeated stochastic predictions estimate both an expected outcome and its variability. The inexpensive surrogate can then support the many evaluations needed inside an optimization loop.

## Two ways to optimize with uncertainty

- **Robust design optimization** balances expected performance with variability. It favors designs whose outcomes remain stable when uncertain inputs change.
- **Reliability-based design optimization** targets the probability of satisfying a performance requirement. It makes an acceptable failure probability part of the decision.

Both approaches shift attention from the best nominal result to performance across plausible conditions. The right formulation depends on whether the decision emphasizes consistent quality, a probability threshold, or both.

## Application to additive manufacturing

In fused filament fabrication, process parameters affect several quality measures at the same time. A data-driven uncertainty model can estimate those outcomes, and a multi-objective optimizer can reveal process settings that balance them. The useful deliverable is not one universal optimum, but a defensible set of trade-offs with uncertainty made visible.

## Practical takeaway

Treat the Pareto front as the beginning of the decision, not the end. Check how the front changes under predictive uncertainty, state the acceptable reliability level, and make the final preference among objectives explicit.

The related paper is [*Multi-objective optimization under uncertainty of part quality in fused filament fabrication*](/publications/2022_kapusuzoglu_asce-asme_journal_of_risk_and_uncertainty_in_engineering_systems_part_b_mechanical_engineering.html). The [publisher record](https://asmedigitalcollection.asme.org/risk/article-abstract/8/1/011112/1129117) contains the complete study.
