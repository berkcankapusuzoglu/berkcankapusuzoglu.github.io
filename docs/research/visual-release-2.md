# Release 2 visual curation backlog

Release 2 has ten candidate figures across seven canonical publications. All remain `rights-review-required`; this document authorizes no asset import or publication. The exact archive entry, source caption, figure number and narrative purpose live in [visual-inventory.yaml](visual-inventory.yaml), under each project's `candidate_entries`.

Release 1 keeps its five approved figures and publication identities. CGD remains the sole homepage research visual, with featured order CGD, expert pruning, SPEAR-MM. Release 2 candidates do not change that order.

## Career-value priority and canonical mapping

Projects at the same priority share a narrative tier. Process optimization is supporting physical context after the required four tiers, rather than a new lead story.

| Priority | Canonical publication | Site slug | Source archive | Career value |
|---|---|---|---|---|
| 1 | [Optimizing Reasoning Efficiency through Prompt Difficulty Prediction](https://openreview.net/pdf/87684b1b0842859502be60986422dd7752b9371d.pdf) | `2025-prompt-difficulty-prediction` | `Reasoning_NeurIPS2025_workshop.zip` | Direct evidence for adaptive inference and efficient reasoning. |
| 2 | [Physics-informed and hybrid machine learning in additive manufacturing: application to fused filament fabrication](https://link.springer.com/article/10.1007/s11837-020-04438-4) | `2020_Kapusuzoglu_Jom` | `PIML.zip` | Establishes the physics-informed ML foundation of the research arc. |
| 2 | [Information fusion and machine learning for sensitivity analysis using physics knowledge and experimental data](https://www.sciencedirect.com/science/article/pii/S0951832021002477) | `2021_Kapusuzoglu_Reliability_Engineering_&_System_Safety` | `PIML-RESS.zip` | Extends that arc through data fusion, uncertainty and sensitivity analysis. |
| 3 | [Multi-objective optimization under uncertainty of part quality in fused filament fabrication](https://asmedigitalcollection.asme.org/risk/article-abstract/8/1/011112/1129117) | `2022_Kapusuzoglu_ASCE-ASME_Journal_of_Risk_and_Uncertainty_in_Engineering_Systems_Part_B_Mechanical_Engineering` | `MultiObj - ASME_RISK-21-1006_final.zip` | Demonstrates decisions among competing objectives under uncertainty. |
| 4 | [Multi-Level Bayesian Calibration of a Multi-Component Dynamic System Model](https://asmedigitalcollection.asme.org/computingengineering/article-abstract/23/1/011006/1145675) | `2023_Kapusuzoglu_Journal_of_Computing_and_Information_Science_in_Engineering` | `MultiLevel - Mitsubishi.zip` | Shows calibration depth below the AI leadership narrative. |
| 4 | [Adaptive surrogate modeling for high-dimensional spatio-temporal output](https://link.springer.com/article/10.1007/s00158-022-03402-x) | `2022_Kapusuzoglu_Structural_and_Multidisciplinary_Optimization` | `Adaptive-Mitsubishi.zip` | Shows efficient modeling of expensive simulations and field outputs. |
| 5 | [Process Optimization Under Uncertainty for Improving the Bond Quality of Polymer Filaments in Fused Filament Fabrication](https://asmedigitalcollection.asme.org/manufacturingscience/article-abstract/143/2/021007/1086236) | `2020_Kapusuzoglu_Journal_of_Manufacturing_Science_and_Engineering` | `Process Optimization Under Uncertainty.zip` | Supplies physical context for the uncertainty and optimization story. |

The process-optimization mapping uses the journal record above. The legacy `2021_Witherell_Paul_Witherell_Berkcan_Kapusuzoglu_Matthew_Sato_Sankaran_Mahadevan` route is a duplicate, not another curation destination. Adaptive surrogate modeling maps to the journal article, not the separate AIAA dimension-reduction paper.

## Candidate extraction paths and acceptance

Paths are case-sensitive entries inside the named nested archive, not repository files. Numbers below follow active archive TeX order; the final paper's number, caption and visual must be compared before approval. Source captions are recorded in the manifest, with markup normalization identified where used.

| Project | Candidate path | Archive figure | Acceptance focus beyond the common gate |
|---|---|---|---|
| Prompt difficulty prediction | `figures/overview.pdf` | 1 | Explain the predictor and routing decision; account for predictor cost rather than promise universal savings. |
| Prompt difficulty prediction | `figures/router_accuracy_predictor_S1.pdf` | 4 | Keep thresholds, baseline points, axes and the s1.1-32B representation source visible; describe only the evaluated setting. |
| Physics-informed and hybrid ML | `Fig4.pdf` | 4 | Preserve all three strategies and distinguish constraints, extra inputs and pre-training. |
| Physics-informed and hybrid ML | `Fig6.pdf` | 6 | Preserve the performance and physical-inconsistency comparison; define each metric near the figure. |
| Information fusion / sensitivity analysis | `PIML_strategies_v2.pdf` | 2 | Preserve all four labelled stages and the distinction between physics and observed data. |
| Multi-objective optimization | `figures/Fig3.pdf` | 3 | Preserve the uncertain prediction and optimization workflow; identify what is measured versus modeled. |
| Multi-objective optimization | `figures/Fig22.pdf` | 22 | Define Case 1 and Monte Carlo simulation; keep objectives, units and uncertainty information intact. |
| Multi-level Bayesian calibration | `figs/figure2.pdf` | 2 | Explain component dependencies and time steps; retain arrows and parameter labels. |
| Adaptive surrogate modeling | `figs/Fig1.pdf` | 1 | Define randomized singular value decomposition and distinguish dimension reduction from adaptive sampling. |
| Process optimization | `FIGs/fig1.pdf` | 1 | Preserve all three bond-formation stages; avoid implying the schematic alone proves optimization gains. |

`Paper Category.zip` is a template with no candidate figures. `SPEAR-MM.zip` is a duplicate/secondary source for `2025-spear-mm`; the reviewed `IEEE-SPEARMM Presentation.zip` remains primary. A fallback requires a fresh figure match and rights review. No candidates are scheduled from either excluded archive.

## Future Research Note briefs

**Adaptive inference.** Reader question: when should a system send a prompt to a larger reasoning model? Use `Reasoning_NeurIPS2025_workshop.zip` / `figures/overview.pdf` (archive Figure 1) from *Optimizing Reasoning Efficiency through Prompt Difficulty Prediction*. Explain how intermediate representations feed a difficulty predictor and guide model selection. The practical takeaway is to evaluate a routing policy against fixed-model baselines and include predictor overhead in the cost calculation. Keep the note within the paper's evaluated tasks; do not turn its routing results into a general guarantee. Draft the note only after this figure clears the rights and final-paper matching gates.

**Scientific ML to LLMs.** Reader question: how has using domain knowledge to supervise learned models shaped the later reasoning work? Use `PIML.zip` / `Fig4.pdf` (archive Figure 4) from *Physics-informed and hybrid machine learning in additive manufacturing: application to fused filament fabrication*. Explain constraints in the loss, physics-model outputs as inputs, and simulation pre-training followed by experimental updates. The practical takeaway is to choose where prior knowledge enters training and evaluate both predictive quality and domain consistency. Connect that design question to CGD's training supervision as a research theme, without claiming that physical constraints and teacher critiques are equivalent mechanisms or that one paper proves the other. Keep the figure blocked until reuse permission is documented.

## Rights and publication gate

Before any legacy or pending candidate moves into `content/publications/<slug>/media/`, replace its project's `license: rights-review-required` with a specific license or permission and record `license_url`, permission scope, evidence, reviewer and review date. Confirm that permission covers the actual figure and intended public web use; author status or access to an Overleaf ZIP is not reuse permission. An unspecified license, empty evidence URL or unresolved scope leaves the gate closed. Update the candidate rights state only after that review.

Then compare the source against the canonical paper, confirm final figure number and caption, and record source checksum, source page, attribution and intended output. Prepare only the approved named entry. Preserve scientific content, including axes, legends, labels and uncertainty bounds. Add alt text, public caption and plain-language takeaway; inspect label readability on mobile and at the largest breakpoint; keep the largest publication derivative at or below 500 KB. Mark an entry `approved` only after every item is recorded and checked. The preparation CLI does not enforce this documentation gate automatically, so the curator must complete it before invoking `prepare` for a backlog asset.

No extraction, conversion, legacy asset move or publishing is part of this backlog task. The private desktop archive remains the source of record, outside Git.
