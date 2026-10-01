# Visual Research Library Design

## Outcome

The portfolio will use selected paper figures to make Berkcan Kapusuzoglu's research legible to AI hiring leaders, researchers, and technical executives without turning the site into a dense proceedings archive.

The visual system will start with the three papers that best support the site's research-led AI leadership position:

1. Critique-Guided Distillation for Robust Reasoning via Refinement.
2. When Load-Balancing Goes Too Far: Expert Pruning in Over-Dispersed Mixture-of-Experts Models.
3. SPEAR-MM: Selective Parameter Evaluation and Restoration via Model Merging for Efficient Financial LLM Adaptation.

The same system will support later visual essays about reasoning efficiency, physics-informed machine learning, uncertainty quantification, and manufacturing optimization.

## Source inventory

The source archive is `C:\Users\berkc\Desktop\Overleaf Projects (12 items).zip`. It contains 12 nested Overleaf project archives and 234 static figure files. It contains no GIF, MP4, or WebM assets.

| Overleaf project | Site record or action | Figure count | Initial recommendation |
| --- | --- | ---: | --- |
| `[ICML_2026] CGD.zip` | `2026-critique-guided-distillation` | 14 | Use `figures/cgd_overview.pdf` as the lead visual and `figures/accuracy_combined.pdf` on the paper page. |
| `MESA_ODI_NeurIPS26.zip` | `2026-load-balancing-expert-pruning` | 10 | Use `figures/ppl_accuracy_scatter.pdf` as the primary result visual; keep entropy and Pareto plots as later options. |
| `IEEE-SPEARMM Presentation.zip` | `2025-spear-mm` | 3 | Use `SPEARMM_pipeline.pdf` and `retention_vs_adaptation_tradeoff.pdf`. This is the preferred visual source for SPEAR-MM. |
| `SPEAR-MM.zip` | `2025-spear-mm` | 4 | Treat as an older/incomplete source and use only if the presentation archive lacks required provenance. |
| `Reasoning_NeurIPS2025_workshop.zip` | `2025-prompt-difficulty-prediction` | 24 | Queue the overview and routing plots for the second release. |
| `PIML-RESS.zip` | `2021_Kapusuzoglu_Reliability_Engineering_&_System_Safety` | 58 | Queue the PIML strategy diagram after reuse rights are verified. |
| `PIML.zip` | `2020_Kapusuzoglu_Jom` | 14 | Queue one physics-informed ML comparison visual after reuse rights are verified. |
| `Process Optimization Under Uncertainty.zip` | `2020_Kapusuzoglu_Journal_of_Manufacturing_Science_and_Engineering` | 41 | Queue the bond-formation schematic or optimization workflow after reuse rights are verified. |
| `MultiObj - ASME_RISK-21-1006_final.zip` | `2022_Kapusuzoglu_ASCE-ASME_Journal_of_Risk_and_Uncertainty_in_Engineering_Systems_Part_B_Mechanical_Engineering` | 25 | Queue the methodology diagram and one Pareto-front result after reuse rights are verified. |
| `MultiLevel - Mitsubishi.zip` | `2023_Kapusuzoglu_Journal_of_Computing_and_Information_Science_in_Engineering` | 16 | Queue the multi-level Bayesian network after reuse rights are verified. |
| `Adaptive-Mitsubishi.zip` | `2022_Kapusuzoglu_Structural_and_Multidisciplinary_Optimization` | 25 | Queue one adaptive-surrogate overview visual after reuse rights are verified. |
| `Paper Category.zip` | None | 0 | Treat as a template, not a publication source. |

The outer archive and nested project archives will remain private source material. They will not be copied into the website repository. Only reviewed, web-ready derivatives and their provenance metadata will be committed.

## Editorial principles

Each visual must answer a visitor question. It cannot exist only to decorate a page.

- A diagram explains how a method works.
- A result plot supports one explicit takeaway.
- An animation explains a sequence or comparison that is harder to understand as a static image.
- Every figure receives a plain-language caption, a one-sentence takeaway, meaningful alt text, and source/licensing metadata.
- A page should normally contain one lead diagram and no more than two supporting result figures.
- Dense plots stay on paper pages or Research Notes; they do not crowd the homepage.

The visual style will preserve the scientific content of the source figure. It may add a consistent frame, caption, step indicator, or highlight overlay, but it will not redraw data, alter scales, remove inconvenient results, or imply a stronger claim than the paper supports.

## Placement

### Homepage

The first featured-research card will show the Critique-Guided Distillation overview. It is the only research figure on the homepage in the initial release. The image should help a recruiter understand the training-to-inference story in a few seconds.

The expert-pruning and SPEAR-MM cards remain typographic. This keeps the hierarchy clear and prevents the homepage from looking like a paper gallery.

### Publication pages

The initial publication-page visual set is:

- CGD: method overview first, combined accuracy result second.
- Expert pruning: perplexity-versus-task-accuracy result first; optional entropy or Pareto result only if the surrounding explanation needs it.
- SPEAR-MM: pipeline first, adaptation-retention frontier second.

Each figure appears next to a short interpretation written for a technical reader who has not read the paper.

The expert-pruning page must use the exact public status: `Accepted at the NeurIPS 2026 Workshop on On-Device Intelligence.` It must not imply a NeurIPS main-track acceptance.

### Research Notes

The first visual Research Note will explain Critique-Guided Distillation as a four-step story:

1. The student produces an initial response.
2. The teacher critiques the failure.
3. The teacher supplies a refined answer.
4. The student learns refinement while inference remains teacher-free.

The note will include the static paper figure, a controllable step sequence derived from it, one results figure, and a concise conclusion. Its core idea and one visual can be adapted into a LinkedIn carousel or post without requiring a separate rewrite of the research argument.

## Motion design

The project archives do not contain animation sources. The first release will therefore create one purposeful motion treatment for the CGD pipeline rather than converting every plot into a GIF.

The animation will be a sequence of optimized static frames rendered by an accessible site component. It will:

- expose Pause and Play controls;
- stop on the explanatory final frame;
- disable automatic motion when `prefers-reduced-motion: reduce` is active;
- keep a static poster visible when JavaScript is unavailable;
- avoid flashing, rapid movement, or decorative looping;
- reuse the paper's factual content without changing the diagram's meaning.

Actual GIF files are not the default because they are heavy, lack native pause controls, and provide a poor reduced-motion experience. Animated WebP or video may be evaluated later only if it materially reduces bytes and retains equivalent controls and fallback behavior.

## Content model

Visual metadata will live with each publication page bundle under a `visuals` front-matter list. A visual entry will have this shape:

```yaml
visuals:
  - id: cgd-overview
    file: media/cgd-overview.png
    role: lead
    alt: "Diagram showing a student response, teacher critique, refined answer, and teacher-free student inference."
    caption: "Critique-Guided Distillation turns teacher critique into training-only supervision."
    takeaway: "The student learns to refine mistakes without requiring the teacher or critique at inference time."
    source_label: "Figure 1"
    source_url: "https://arxiv.org/abs/2505.11628"
    license: "CC BY 4.0"
    homepage: true
```

Sequence metadata will extend the same entry:

```yaml
    sequence:
      interval_ms: 2400
      frames:
        - file: media/cgd-step-1.png
          label: "1. Initial response"
        - file: media/cgd-step-2.png
          label: "2. Teacher critique"
        - file: media/cgd-step-3.png
          label: "3. Refined answer"
        - file: media/cgd-step-4.png
          label: "4. Teacher-free inference"
```

Required fields are `id`, `file`, `role`, `alt`, `caption`, `takeaway`, `source_label`, `source_url`, and `license`. Sequence frames require a local file and visible label. Publication pages use local page resources; remote images are not allowed.

## Asset workflow

A small import tool will inventory nested ZIP files without extracting the full archive. A separate preparation command will extract only a named figure from a named nested project, rasterize the selected PDF with Poppler, and emit a source PNG into the correct publication page bundle.

Hugo will generate responsive WebP derivatives during the site build. The committed source PNG preserves sufficient detail for future sizes without committing the original Overleaf archive or all 234 figures.

The curation manifest will record:

- outer archive checksum;
- nested project and original figure path;
- mapped publication slug;
- source figure number and caption;
- public source URL;
- reuse license or `rights-review-required`;
- selection status: `selected`, `backlog`, `duplicate`, `template`, or `rejected`;
- a short reason for the decision.

Older publisher-owned papers remain in the backlog until reuse rights are verified. Being an author is not treated as automatic permission to republish a publisher-formatted figure.

## Components

The site will add:

- `research-figure.html` for static figures, responsive image generation, captions, takeaways, and source attribution;
- `research-sequence.html` for controllable step-by-step explainers;
- a small `research-visuals.js` controller for Play/Pause, frame changes, and reduced-motion handling;
- CSS for full-width lead figures, narrower result plots, captions, controls, and print behavior.

Publication cards will accept an explicit `homepage: true` visual. Only the first featured CGD card will render one in the initial release.

## Performance and accessibility budgets

- The homepage visual should be no more than 250 KB at its largest delivered breakpoint.
- A publication-page responsive image should normally be no more than 500 KB at its largest delivered breakpoint.
- Below-the-fold figures use native lazy loading.
- Images include intrinsic width and height to avoid layout shift.
- Alt text describes the information conveyed; captions do not merely repeat it.
- Plot interpretation is also available in nearby prose, so color or image access is not required to understand the claim.
- Color is never the only encoding added by the site.
- Sequence controls are keyboard accessible and have clear accessible names.
- Print output uses the static final frame and includes the source attribution.

## Search, sharing, and LinkedIn reuse

The CGD lead figure may be used as the social preview for the paper page and first Research Note after it is checked at the target crop. Social images will be local, have a 1.91:1 derivative, and retain legible type.

Research Notes will expose a short plain-language thesis, two or three takeaways, and a canonical URL. The README will document how to turn that material into a LinkedIn post or carousel while linking back to the site.

## Release sequence

### Release 1: signature AI work

- Add the reusable visual schema and components.
- Publish CGD, expert-pruning, and SPEAR-MM visuals.
- Correct the expert-pruning workshop acceptance status.
- Publish the first CGD visual Research Note.
- Add the CGD sequence explainer.

### Release 2: efficient reasoning and scientific ML depth

- Add the prompt-difficulty overview and routing result.
- Add one visual each for PIML/RESS, multi-objective optimization, multi-level Bayesian calibration, and adaptive surrogate modeling, subject to rights review.
- Create a second Research Note around adaptive inference or model routing.

### Release 3: optional visual archive

- Add selected legacy visuals only where they improve the story.
- Do not aim to publish all 234 figures.
- Consider a visual index only after at least six publication pages have high-quality contextual explanations.

## Success criteria

The release succeeds when:

1. A recruiter can understand the CGD idea from the homepage visual and card copy in under 15 seconds.
2. Each of the three lead AI papers has a coherent method/result story rather than an unexplained figure dump.
3. The first Research Note is substantive enough to share on LinkedIn.
4. Motion is optional, controllable, and disabled for reduced-motion users.
5. Every published visual has recorded provenance and reuse rights.
6. Berkcan can add a future figure by following one documented command-and-front-matter workflow.

## Out of scope

- Committing the full Overleaf archive or all nested ZIPs.
- Publishing every figure in every paper.
- Recreating plots from raw experimental data in the first release.
- Animating scientific result charts merely for visual interest.
- Publishing figures with unresolved reuse rights.
- Adding a CMS or server-side image service.
