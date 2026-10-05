---
title: "Uncertainty Quantification (UQ) and Sensitivity Analysis: Part I"
date: 2022-04-20
description: "An introduction to uncertainty quantification, global sensitivity analysis, and their role in damage prognosis and decision-making."
summary: "Uncertainty quantification asks how uncertain a prediction is, while sensitivity analysis identifies which uncertain inputs contribute most to that result."
original_url: "https://medium.com/@berkcan1992/uncertainty-quantification-uq-and-sensitivity-analysis-part-i-2e7078e9136c"
---

*Originally published on Medium in 2022. This archive edition summarizes the central ideas. [Read the original on Medium](https://medium.com/@berkcan1992/uncertainty-quantification-uq-and-sensitivity-analysis-part-i-2e7078e9136c).*

## Two questions, one decision problem

Uncertainty quantification asks how much confidence we should place in a model prediction. Sensitivity analysis asks which uncertain inputs are responsible for the variation in that prediction. Together, they turn a single forecast into information a decision-maker can inspect.

This matters in fatigue-damage prognosis. Measurements are noisy, material and loading conditions vary, model parameters are imperfectly known, and the damage state itself may be only partially observed. Reporting one predicted remaining-life value hides those sources of uncertainty.

## Aleatory and epistemic uncertainty

Two categories help organize the problem:

- **Aleatory uncertainty** describes inherent variability, such as changing loads or differences among nominally similar components.
- **Epistemic uncertainty** describes limited knowledge, such as uncertain model parameters, sparse observations, or an imperfect damage-growth model.

The distinction affects what to do next. More data or a better model can reduce epistemic uncertainty. Aleatory variability generally must be represented and managed rather than eliminated.

## Sensitivity analysis identifies what matters

Global sensitivity analysis evaluates inputs across their ranges rather than only near one nominal setting. Variance-based measures such as Sobol indices can separate individual effects from interactions among inputs. The result is a ranked view of which uncertainties drive the predicted quantity of interest.

That ranking supports model development and test planning. If one uncertain parameter dominates the prognosis, a new measurement can target that parameter. If an input has negligible influence, modeling it in greater detail may add cost without improving the decision.

## From diagnosis to prognosis

A damage-management workflow can combine probabilistic diagnosis, Bayesian updating, and prognosis. Measurements update uncertain states or parameters as evidence arrives. Sequential methods such as particle filtering help carry that uncertainty forward through a nonlinear damage model. Sensitivity analysis then explains which assumptions or measurements have the strongest effect on the predicted outcome.

## Practical takeaway

Do not treat uncertainty as a single error bar added after prediction. Trace each source through the model, separate reducible knowledge gaps from inherent variability, and use sensitivity results to decide what to measure or improve next.

Related publications include [*Information fusion and machine learning for sensitivity analysis using physics knowledge and experimental data*](/publications/2021_kapusuzoglu_reliability_engineering__system_safety.html) and [*Digital twin approach for intelligent operation planning and health management of mechanical systems*](/publications/2020_karve_annual_conference_of_the_phm_society.html).
