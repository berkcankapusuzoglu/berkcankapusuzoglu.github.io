# Visual Research Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn selected Overleaf paper figures into an accessible, high-performance visual research system that strengthens Berkcan Kapusuzoglu's positioning for AI leadership roles.

**Architecture:** Keep source archives outside the repository, inventory them through a read-only nested-ZIP tool, and import only reviewed figures into Hugo publication page bundles. Publication front matter owns visual metadata; local Hugo partials render responsive figures and a controllable frame sequence; the existing Python/Hugo checks enforce provenance, accessibility, local assets, and performance budgets.

**Tech Stack:** Hugo Extended 0.145.0, Go templates, Markdown/YAML page bundles, vanilla CSS and JavaScript, Python 3 standard library for archive inventory, Poppler `pdftoppm` for PDF rasterization, optional Pillow for curated sequence-frame preparation, existing unittest and Pa11y CI checks.

**Spec:** `docs/superpowers/specs/2026-10-01-visual-research-library-design.md`

## Global constraints

- Keep `C:\Users\berkc\Desktop\Overleaf Projects (12 items).zip` and its 12 nested archives out of Git.
- Never bulk-extract the archive into the repository. Extract only an explicitly selected source figure.
- Commit only reviewed web-source images, metadata, and generated site code.
- Use Critique-Guided Distillation as the first and only homepage research visual in Release 1.
- Keep featured-research order: CGD, expert pruning, SPEAR-MM.
- Label the pruning paper exactly as accepted at the NeurIPS 2026 Workshop on On-Device Intelligence; never imply main-track NeurIPS acceptance.
- Do not publish an older journal figure until its reuse rights are recorded as approved.
- Do not alter data, axes, legends, or experimental meaning when preparing an image.
- Every figure requires alt text, a caption, a plain-language takeaway, a source label and URL, and a reuse license.
- Every animated sequence requires Play/Pause, a no-JavaScript poster, and reduced-motion behavior.
- Keep the homepage image at or below 250 KB and publication-page responsive images at or below 500 KB per largest delivered breakpoint.
- Keep existing public routes and the current portrait/intro intact.
- Use focused commits after each task; do not mix legacy-theme cleanup or unrelated résumé edits into this plan.

## Review focus

- Missing or misspelled local image paths must fail the Hugo build.
- A visual without provenance, alt text, or a takeaway must fail validation.
- A sequence must remain understandable with JavaScript disabled and with reduced motion enabled.
- The homepage must never render more than one research image in this release.
- Dense plots must not appear without nearby interpretation.
- Source ZIPs, intermediate extraction directories, and unlicensed figures must never appear in `git status`.

---

### Task 1: Record the archive inventory and curation decisions

**Files:**
- Create: `scripts/research_assets.py`
- Create: `tests/test_research_assets.py`
- Create: `docs/research/visual-inventory.yaml`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `inventory_archive(archive: pathlib.Path) -> list[ProjectRecord]`
- Produces: `select_entry(archive, project_name, entry_name, destination) -> pathlib.Path`
- Produces CLI: `python scripts/research_assets.py inventory --archive <outer.zip>`
- Produces CLI: `python scripts/research_assets.py extract --archive <outer.zip> --project <nested.zip> --entry <figure.pdf> --output <path>`
- Consumes: one outer ZIP containing nested Overleaf ZIPs

- [ ] **Step 1: Write failing nested-ZIP tests**

Use `tempfile` and `zipfile` to create a tiny outer archive containing two nested project ZIPs. Add tests proving the inventory returns project names, figure paths, extensions, uncompressed sizes, and counts without writing extracted files to disk. Add failure tests for an unknown nested project, unknown figure path, path traversal such as `../outside.pdf`, and a non-ZIP outer file.

- [ ] **Step 2: Run the tests and confirm failure**

Run:

```powershell
python -m unittest tests.test_research_assets -v
```

Expected: FAIL because `scripts.research_assets` does not exist.

- [ ] **Step 3: Implement read-only inventory and safe single-file extraction**

Use only Python's standard library. Open nested ZIPs through `io.BytesIO`; do not extract whole projects. Normalize archive paths with `PurePosixPath`, reject absolute paths and `..`, and create the destination parent only after both project and entry are validated.

The inventory command emits deterministic YAML-compatible text sorted by nested project and figure path. Include SHA-256 for the outer archive and each selected entry.

- [ ] **Step 4: Create the curated manifest**

Add all 12 project archives to `docs/research/visual-inventory.yaml`. Record the 234-figure total and classify each project as `selected`, `backlog`, `duplicate`, or `template`. At minimum, record these Release 1 source paths:

- `[ICML_2026] CGD.zip` / `figures/cgd_overview.pdf`
- `[ICML_2026] CGD.zip` / `figures/accuracy_combined.pdf`
- `MESA_ODI_NeurIPS26.zip` / `figures/ppl_accuracy_scatter.pdf`
- `IEEE-SPEARMM Presentation.zip` / `SPEARMM_pipeline.pdf`
- `IEEE-SPEARMM Presentation.zip` / `retention_vs_adaptation_tradeoff.pdf`

Record `rights-review-required` for older journal figures until verified. Record the recent arXiv license only after checking the canonical paper page.

- [ ] **Step 5: Protect private and temporary sources**

Add ignore rules for `*.zip` only if the repository does not intentionally track other ZIP artifacts; otherwise add narrow rules for `research-source/`, `asset-work/`, and the archive name. Ensure temporary PDF/PNG conversion outputs cannot be committed accidentally.

- [ ] **Step 6: Verify against the real archive**

Run:

```powershell
python scripts/research_assets.py inventory --archive "C:\Users\berkc\Desktop\Overleaf Projects (12 items).zip"
python -m unittest tests.test_research_assets -v
git status --short
```

Expected: 12 projects, 234 static figure files, zero motion files, all tests PASS, and no source archive or temporary extraction appears in Git.

- [ ] **Step 7: Commit**

```powershell
git add .gitignore scripts/research_assets.py tests/test_research_assets.py docs/research/visual-inventory.yaml
git commit -m "build: inventory curated paper visuals"
```

---

### Task 2: Add a validated visual metadata contract

**Files:**
- Create: `layouts/partials/research-visual-validate.html`
- Modify: `layouts/partials/publication-validate.html`
- Modify: `archetypes/publications.md`
- Modify: `scripts/site_check.py`
- Modify: `tests/test_site_check.py`

**Interfaces:**
- Consumes publication `visuals[]` fields: `id`, `file`, `role`, `alt`, `caption`, `takeaway`, `source_label`, `source_url`, `license`, optional `homepage`, optional `sequence`
- Produces Hugo build errors for missing fields, duplicate visual IDs, remote files, missing page resources, or invalid roles
- Produces generated-HTML validation for visual accessibility and local asset use

- [ ] **Step 1: Add failing validation fixtures**

Add fixture pages that fail for:

- missing `alt`, `caption`, `takeaway`, `source_url`, or `license`;
- a remote `file` URL;
- a missing page resource;
- duplicate visual IDs;
- an unsupported role;
- a sequence with fewer than two frames;
- a sequence frame with no label or local file;
- more than one `homepage: true` visual across featured publications.

- [ ] **Step 2: Run the focused tests and confirm failure**

Run:

```powershell
python -m unittest tests.test_site_check -v
```

Expected: FAIL on the new visual-contract cases.

- [ ] **Step 3: Implement Hugo front-matter validation**

Create `research-visual-validate.html` and call it from publication validation. Use `errorf` with the publication path and visual ID. Resolve every `file` and sequence-frame path through `.Resources.GetMatch`; error if the file is absent. Allow roles `lead`, `result`, and `supporting`.

- [ ] **Step 4: Extend generated-site checks**

Teach `site_check.py` to reject remote image sources in research figures, figures without a `figcaption`, sequence containers without a control button, and images missing intrinsic dimensions. Preserve existing decorative-image behavior.

- [ ] **Step 5: Document the schema in the archetype**

Add a commented example visual entry to `archetypes/publications.md`. Keep visuals optional so older records continue to build.

- [ ] **Step 6: Verify and commit**

Run the Python tests and Hugo build, then commit:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
hugo --cleanDestinationDir --minify --panicOnWarning --printPathWarnings
git add layouts/partials/research-visual-validate.html layouts/partials/publication-validate.html archetypes/publications.md scripts/site_check.py tests/test_site_check.py
git commit -m "feat: validate publication visual metadata"
```

---

### Task 3: Build reusable static and sequence figure components

**Files:**
- Create: `layouts/partials/research-figure.html`
- Create: `layouts/partials/research-sequence.html`
- Create: `assets/js/research-visuals.js`
- Modify: `layouts/partials/head.html`
- Modify: `assets/css/main.css`
- Modify: `tests/test_site_check.py`
- Modify: `scripts/check_a11y.mjs`

**Interfaces:**
- `research-figure.html` receives `{Page, Visual, Context}` and renders a responsive local page resource
- `research-sequence.html` receives `{Page, Visual}` and renders a poster, labelled frames, status text, and Play/Pause control
- `research-visuals.js` initializes `[data-research-sequence]` elements and exposes no globals

- [ ] **Step 1: Add failing component-output tests**

Assert that a representative static figure produces `figure`, responsive image sources, intrinsic dimensions, lazy loading below the fold, a visible takeaway, caption, and linked source/license attribution. Assert that a sequence produces a poster without JavaScript, a real button with an accessible name, frame labels, and a polite status region.

- [ ] **Step 2: Add failing reduced-motion tests**

Add a JavaScript syntax check and a lightweight DOM fixture or Pa11y assertion proving the sequence does not auto-advance when `matchMedia('(prefers-reduced-motion: reduce)')` matches. Require the static final/poster frame in print CSS.

- [ ] **Step 3: Implement the static figure partial**

Use Hugo image processing to create width-limited WebP derivatives at practical breakpoints such as 640, 960, and 1440 pixels. Keep the original resource as a fallback. Render a `<picture>` with dimensions and appropriate loading priority: eager only for the one homepage lead visual, lazy elsewhere.

- [ ] **Step 4: Implement the sequence partial and controller**

Render all frames as local responsive resources, show the final explanatory poster before initialization, and add a Play/Pause button. The controller advances one labelled frame at a time, stops after the final frame by default, pauses when the tab is hidden, and responds to reduced-motion changes at runtime.

- [ ] **Step 5: Add editorial figure styling**

Add restrained framing, a plot-safe light surface, readable captions, source attribution, a high-contrast active-step indicator, and mobile stacking. Avoid shadows and decorative chrome that compete with scientific content.

- [ ] **Step 6: Load JavaScript only where needed**

In `head.html`, include the fingerprinted sequence script only when the page contains sequence metadata. Keep all static-figure pages JavaScript-free.

- [ ] **Step 7: Verify and commit**

Run unit tests, Hugo, JavaScript syntax, and Pa11y. Inspect keyboard control and reduced motion at 360x800 and 1440x900.

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
hugo --cleanDestinationDir --minify --panicOnWarning --printPathWarnings
node --check assets/js/research-visuals.js
npm run check:a11y
git add layouts/partials/research-figure.html layouts/partials/research-sequence.html layouts/partials/head.html assets/css/main.css assets/js/research-visuals.js tests/test_site_check.py scripts/check_a11y.mjs
git commit -m "feat: add accessible research figure components"
```

---

### Task 4: Import and prepare the five Release 1 source figures

**Files:**
- Modify: `scripts/research_assets.py`
- Modify: `tests/test_research_assets.py`
- Create: `content/publications/2026-critique-guided-distillation/media/cgd-overview.png`
- Create: `content/publications/2026-critique-guided-distillation/media/cgd-accuracy.png`
- Create: `content/publications/2026-load-balancing-expert-pruning/media/ppl-accuracy.png`
- Create: `content/publications/2025-spear-mm/media/spear-pipeline.png`
- Create: `content/publications/2025-spear-mm/media/retention-adaptation.png`
- Modify: `docs/research/visual-inventory.yaml`

**Interfaces:**
- Produces CLI: `python scripts/research_assets.py prepare --archive <outer.zip> --project <nested.zip> --entry <figure.pdf> --output <png> [--dpi 180]`
- Invokes: `pdftoppm -singlefile -png -r <dpi> <input.pdf> <output-prefix>`
- Verifies: raster dimensions, output existence, and deterministic source checksum metadata

- [ ] **Step 1: Add failing command-construction and error tests**

Mock the Poppler subprocess and assert safe argument-list invocation, no shell interpolation, correct `-singlefile`, DPI bounds, and failure when Poppler is absent or output is missing. Reject output outside the repository's `content/publications/` tree.

- [ ] **Step 2: Implement the preparation command**

Extract the selected PDF to a temporary directory, call Poppler with an argument list, and move only the resulting PNG to the explicit publication bundle. Always remove temporary files. Do not overwrite an existing asset unless `--replace` is explicitly supplied.

- [ ] **Step 3: Generate the five source PNGs**

Run the preparation command once for each selected source listed in Task 1. Use a DPI that keeps plot labels readable on a 1440-pixel derivative. Inspect every generated image at original resolution before committing.

- [ ] **Step 4: Check factual fidelity and cropping**

Confirm that titles, axes, legends, confidence intervals, and annotations match the paper source. Crop only excess page whitespace; do not crop legends or contextual labels. If the PDF has multiple pages, explicitly select the correct page and record it in the manifest.

- [ ] **Step 5: Update provenance records**

For each output, record output path, dimensions, source checksum, paper URL, figure number, original caption, selected public caption, and license. Do not mark a visual `approved` until all fields are present.

- [ ] **Step 6: Verify repository hygiene and commit**

Run:

```powershell
python -m unittest tests.test_research_assets -v
git status --short
git check-attr --all -- "*.zip"
```

Expected: only five PNGs, the script/test changes, and the manifest are added; no ZIPs, PDFs, or temporary conversion directories appear.

```powershell
git add scripts/research_assets.py tests/test_research_assets.py docs/research/visual-inventory.yaml content/publications/*/media
git commit -m "assets: add curated lead paper figures"
```

---

### Task 5: Publish the three visual paper stories and the homepage lead visual

**Files:**
- Modify: `content/publications/2026-critique-guided-distillation/index.md`
- Modify: `content/publications/2026-load-balancing-expert-pruning/index.md`
- Modify: `content/publications/2025-spear-mm/index.md`
- Modify: `layouts/publications/single.html`
- Modify: `layouts/partials/publication-card.html`
- Modify: `layouts/index.html`
- Modify: `assets/css/main.css`
- Modify: `tests/test_site_check.py`

**Interfaces:**
- Publication pages render `visuals` in declared order with interpretation adjacent to each figure
- Homepage card renders only the first featured publication visual with `homepage: true`
- Publication status and venue render from structured front matter

- [ ] **Step 1: Add failing generated-page assertions**

Assert:

- the homepage contains exactly one `[data-research-visual]` and it belongs to CGD;
- CGD detail renders the overview before the accuracy plot;
- expert pruning renders the PPL/accuracy plot and the exact ODI workshop acceptance label;
- SPEAR-MM renders the pipeline before the adaptation-retention plot;
- each figure is followed by a visible takeaway and attribution;
- no featured card other than CGD contains an image.

- [ ] **Step 2: Add the visual metadata and interpretation copy**

Write concise, non-promotional alt text, captions, and takeaways grounded in each paper. Do not repeat the abstract. Use the paper's exact scope when describing results.

- [ ] **Step 3: Correct expert-pruning publication metadata**

Set the venue to `NeurIPS 2026 Workshop on On-Device Intelligence`, type `workshop`, and status `accepted`, using the canonical paper/workshop source. Keep the summary focused on why router importance becomes unreliable under over-dispersion and what domain-aware allocation changes.

- [ ] **Step 4: Render figures on publication pages**

Update `publications/single.html` to place the lead visual after the high-level research contribution and result visuals after short explanatory subheads. Preserve all existing links and canonical metadata.

- [ ] **Step 5: Render the CGD homepage visual**

Update the featured card or homepage template so only the CGD `homepage: true` visual appears. Give it enough width to remain legible without displacing the paper title, venue, or links.

- [ ] **Step 6: Build and inspect**

Run the full test suite and inspect the homepage plus all three publication pages at mobile and desktop widths. Verify that no plot label is unreadable, no card overflows, and no figure causes layout shift.

- [ ] **Step 7: Commit**

```powershell
git add content/publications/2026-critique-guided-distillation content/publications/2026-load-balancing-expert-pruning content/publications/2025-spear-mm layouts/publications/single.html layouts/partials/publication-card.html layouts/index.html assets/css/main.css tests/test_site_check.py
git commit -m "content: publish visual stories for featured research"
```

---

### Task 6: Create the CGD step sequence and first visual Research Note

**Files:**
- Modify: `scripts/research_assets.py`
- Modify: `tests/test_research_assets.py`
- Create: `content/writing/critique-guided-distillation-refinement/index.md`
- Create: `content/writing/critique-guided-distillation-refinement/media/cgd-step-1.png`
- Create: `content/writing/critique-guided-distillation-refinement/media/cgd-step-2.png`
- Create: `content/writing/critique-guided-distillation-refinement/media/cgd-step-3.png`
- Create: `content/writing/critique-guided-distillation-refinement/media/cgd-step-4.png`
- Modify: `layouts/_default/single.html`
- Modify: `layouts/writing/list.html`
- Modify: `assets/css/main.css`
- Modify: `tests/test_site_check.py`

**Interfaces:**
- Produces CLI: `python scripts/research_assets.py sequence --source <png> --recipe <yaml> --output-dir <dir>`
- Sequence recipe defines ordered labels and non-destructive highlight/crop regions
- Research Note uses the same visual front-matter contract or a documented note-specific subset

- [ ] **Step 1: Write failing sequence-recipe tests**

Test recipe parsing, fixed frame order, bounds checking, nonzero durations, output-name safety, and deterministic dimensions. Keep Pillow import lazy so inventory commands continue to work without it.

- [ ] **Step 2: Implement non-destructive frame preparation**

Use the bundled Pillow runtime or documented `requirements-assets.txt` only for this authoring command. Each frame must preserve the complete underlying diagram and add a restrained highlight plus visible step label; do not erase context or redraw the scientific content.

- [ ] **Step 3: Produce and review four CGD frames**

Create frames for initial student response, teacher critique, refined answer, and teacher-free inference. Check the sequence at 360px and ensure every label remains readable. Keep the final frame as the no-JavaScript and reduced-motion poster.

- [ ] **Step 4: Write the Research Note**

Use this structure:

1. The problem: outcome-only distillation hides why an answer failed.
2. The method: critique becomes training-only supervision.
3. The four-step sequence.
4. What the accuracy result does and does not establish.
5. The practical takeaway for robust reasoning systems.
6. Paper link and citation.

Write for an AI research/engineering audience, not as a paper abstract. Avoid unverified internal results or employer-sensitive implementation details.

- [ ] **Step 5: Add LinkedIn-ready metadata**

Add a short thesis and two or three shareable takeaways in front matter. Do not render a hidden keyword dump. Document that the LinkedIn post should link to this canonical note rather than reproduce the entire article.

- [ ] **Step 6: Render and verify the note**

Ensure the standard single-page template renders figures and sequence metadata for Research Notes. Confirm the writing index now lists the real note instead of the empty state. Test Play/Pause, no-JavaScript, reduced-motion, keyboard behavior, and print output.

- [ ] **Step 7: Commit**

```powershell
git add scripts/research_assets.py tests/test_research_assets.py content/writing/critique-guided-distillation-refinement layouts/_default/single.html layouts/writing/list.html assets/css/main.css tests/test_site_check.py
git commit -m "content: add visual note on critique-guided distillation"
```

---

### Task 7: Build the second-release curation backlog without publishing unreviewed figures

**Files:**
- Modify: `docs/research/visual-inventory.yaml`
- Create: `docs/research/visual-release-2.md`
- Modify: `docs/research/publication-sources.md`

**Interfaces:**
- Maps each viable Overleaf project to one canonical site publication and at most two candidate figures
- Records rights state, narrative purpose, extraction path, and acceptance criteria

- [ ] **Step 1: Map the remaining projects**

Record exact paper title, site slug, canonical paper URL, candidate figure path, figure number/caption, and purpose for:

- prompt difficulty prediction;
- physics-informed and hybrid ML;
- information fusion/sensitivity analysis;
- process optimization under uncertainty;
- multi-objective optimization under uncertainty;
- multi-level Bayesian calibration;
- adaptive surrogate modeling.

Mark `Paper Category.zip` as a template and `SPEAR-MM.zip` as a duplicate/secondary source.

- [ ] **Step 2: Rank by career value**

Use this release priority:

1. Prompt difficulty prediction: directly supports adaptive inference and efficient reasoning.
2. PIML/RESS: shows the research arc from physics-informed ML to modern foundation-model work.
3. Multi-objective optimization: demonstrates decision-making under uncertainty.
4. Multi-level Bayesian calibration and adaptive surrogate modeling: demonstrate depth, but belong below the AI leadership narrative.

- [ ] **Step 3: Define one future note per theme**

Add a one-paragraph brief for an adaptive-inference note and a scientific-ML-to-LLMs note. Each brief must name the reader question, one source figure, one practical takeaway, and the supporting publication.

- [ ] **Step 4: Verify rights gates**

No legacy asset moves into a publication bundle until `license` changes from `rights-review-required` to a specific permission or license with a source URL.

- [ ] **Step 5: Commit**

```powershell
git add docs/research/visual-inventory.yaml docs/research/visual-release-2.md docs/research/publication-sources.md
git commit -m "docs: prioritize the visual research backlog"
```

---

### Task 8: Teach the owner workflow

**Files:**
- Modify: `README.md`
- Create: `docs/research/adding-a-paper-visual.md`
- Create: `docs/research/publishing-a-visual-note.md`
- Modify: `archetypes/publications.md`

**Interfaces:**
- Documents archive inventory, safe extraction, PDF preparation, front matter, local preview, validation, deployment, and rollback
- Documents how to reuse one note for LinkedIn without changing the canonical source

- [ ] **Step 1: Add the five-minute visual update path**

Document the exact commands to:

1. preview the archive inventory;
2. prepare one named figure;
3. add the visual metadata;
4. preview with `hugo server`;
5. run tests;
6. commit and deploy.

Explain which fields the owner may safely edit and which claims/licenses require verification.

- [ ] **Step 2: Add a visual-note template**

Document a repeatable note structure: reader question, diagram, interpretation, result, limits, takeaway, citation. Include the front-matter sequence example and a LinkedIn adaptation checklist.

- [ ] **Step 3: Document image quality and accessibility checks**

Include practical checks for label readability, alt text, color independence, source attribution, mobile layout, bytes, reduced motion, and no confidential annotations in exported figures.

- [ ] **Step 4: Dry-run the instructions**

Follow the guide against a disposable temporary publication bundle without committing it. Fix every ambiguous path or missing prerequisite.

- [ ] **Step 5: Commit**

```powershell
git add README.md docs/research/adding-a-paper-visual.md docs/research/publishing-a-visual-note.md archetypes/publications.md
git commit -m "docs: explain the research visual workflow"
```

---

### Task 9: Run the release gate and external-recruiter review

**Files:**
- Modify as needed from findings: `content/`, `layouts/`, `assets/`, `scripts/`, `tests/`, `docs/`

- [ ] **Step 1: Run all automated checks**

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
hugo --cleanDestinationDir --minify --panicOnWarning --printPathWarnings
python scripts/site_check.py --public public --expected tests/expected-urls.txt
node --check assets/js/research-visuals.js
npm ci
npm run check:a11y
git diff --check
```

Expected: every command exits 0.

- [ ] **Step 2: Check asset budgets**

Confirm the generated homepage visual is at or below 250 KB and every largest publication derivative is at or below 500 KB. Confirm source PNGs are reasonable repository assets and no archive/intermediate file is tracked.

- [ ] **Step 3: Inspect the complete experience**

At 360x800 and 1440x900, review:

- homepage with the original portrait and intro;
- all three featured-research cards;
- CGD, expert-pruning, and SPEAR-MM detail pages;
- Research Notes index and the CGD note;
- keyboard-only sequence control;
- reduced motion, no JavaScript, and print preview;
- dark/high-contrast browser modes if supported by the current site.

- [ ] **Step 4: Run an external-recruiter pass**

Ask a reviewing agent to evaluate only the generated site, not the implementation. The reviewer must answer:

1. Is Berkcan's research-led AI leadership positioning clear in 30 seconds?
2. Does CGD remain the unmistakable lead work?
3. Do visuals clarify the work or make the site feel like a paper dump?
4. Is the expert-pruning workshop status precise?
5. Is the Research Note strong enough to share on LinkedIn?
6. What is the single highest-impact remaining change?

Apply only evidence-based findings inside the approved scope.

- [ ] **Step 5: Preview before push**

Serve the final branch locally and let Berkcan review it at `http://localhost:1313/`. Do not push or open a pull request until Berkcan approves the companion preview.

- [ ] **Step 6: Final commit and handoff**

If review fixes were required, commit them separately:

```powershell
git add content layouts assets scripts tests docs README.md
git commit -m "fix: polish the visual research experience"
```

Report the branch, commits, checks, preview URL, five selected source figures, and the Release 2 backlog. Keep the desktop archive unchanged.

## Expected release result

- The homepage still looks like Berkcan's site, including the existing portrait and introduction.
- CGD remains the top featured research item and gains the only homepage figure.
- CGD, expert pruning, and SPEAR-MM each have an interpretable visual story.
- Expert pruning is accurately labeled as accepted at the NeurIPS 2026 ODI workshop.
- Research Notes contains a real CGD visual essay suitable for LinkedIn reuse.
- The archive is mapped, private, and reproducible without being committed.
- Adding another paper visual becomes a documented owner workflow rather than an ad hoc redesign.
