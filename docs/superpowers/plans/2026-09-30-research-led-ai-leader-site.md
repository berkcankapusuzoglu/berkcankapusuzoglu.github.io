# Research-led AI Leader Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the legacy academic-template site with a maintainable Hugo portfolio that positions Berkcan Kapusuzoglu as a research-led AI technical leader.

**Architecture:** Keep Hugo and GitHub Pages, preserve existing public URLs, and replace Wowchemy with a small local renderer. Markdown page bundles remain the content source of truth, `data/profile.yaml` holds shared identity and proof points, and a small Python validation harness checks generated HTML without becoming a runtime dependency.

**Tech Stack:** Hugo Extended 0.145.0, Go templates, YAML/Markdown, vanilla CSS, minimal vanilla JavaScript, Python 3 standard library tests, GitHub Actions, Pa11y CI for automated accessibility checks.

**Spec:** `docs/superpowers/specs/2026-09-30-research-led-ai-leader-site-design.md`

## Global Constraints

- Preserve the public domain and all meaningful currently indexed `.html` URLs during this migration. Blank gallery routes and the unused CMS admin route may be retired and recorded explicitly.
- Keep the production site fully static and buildable with Hugo Extended 0.145.0; Node is allowed only for CI accessibility testing.
- Use the official title `Staff Applied Researcher - AI Foundations`.
- Feature research in this order: Critique-Guided Distillation, expert pruning in over-dispersed MoE models, then SPEAR-MM.
- Label every publication as main conference, workshop, proceedings paper, preprint, accepted, or under review based on a primary source.
- Do not publish the résumé phone number, ZIP code, internal business-unit names, private benchmarks, or unapproved internal-system details.
- Default to paper-backed evidence. Omit the 2,048-GPU, 15B-120B, internal compression, financial-impact, and internal model-performance claims unless Berkcan separately confirms public-use approval.
- Do not describe a workshop paper as a main-track conference paper.
- Do not replace `static/files/resume/Berkcan_Resume.pdf` until a freshly compiled PDF from the approved résumé source is available and visually checked.
- Use one meaningful H1 per page, semantic landmarks, keyboard-visible focus, accessible link names, useful alt text, and reduced-motion behavior.
- Keep the site build free of remote runtime scripts except deliberately approved analytics or fonts; the initial implementation uses no analytics and no remote fonts.
- Use focused commits after each task and do not mix unrelated cleanup into a task.

## Review Focus

- A legacy bookmarked `.html` URL must still resolve after the local renderer replaces Wowchemy; Task 1 pins the URL set and Task 7 rechecks it.
- A publication with a missing venue type or status must fail the build instead of rendering an ambiguous citation; Task 3 adds this failure test.
- The homepage must keep Critique-Guided Distillation first even if publication dates change; Task 4 tests explicit featured weights.
- Social links and the navigation must remain usable without a mouse and visible to assistive technology; Tasks 2 and 7 test landmarks, focus, and accessible labels.
- Long author lists and paper titles must wrap without horizontal overflow at 360px; Tasks 3 and 7 include mobile rendering checks.

---

### Task 1: Establish the reproducible build and compatibility gate

**Files:**
- Create: `scripts/site_check.py`
- Create: `tests/test_site_check.py`
- Create: `tests/expected-urls.txt`
- Modify: `.github/workflows/gh-pages.yml`
- Modify: `hugo.toml`

**Interfaces:**
- Produces: `collect_html_routes(public_dir: pathlib.Path) -> set[str]`
- Produces: `validate_expected_routes(actual: set[str], expected_file: pathlib.Path) -> list[str]`
- Produces: `validate_html_document(path: pathlib.Path) -> list[str]`
- Produces: CLI `python scripts/site_check.py --public public --expected tests/expected-urls.txt`
- Consumes: Hugo output in `public/`

- [ ] **Step 1: Capture the current URL contract**

Build the unmodified site with `hugo --minify`, convert every generated HTML path into a leading-slash route, and store the sorted set in `tests/expected-urls.txt`. Exclude generated search-index data but include the homepage, publication pages, publication list, RSS-independent HTML, and 404 page.

- [ ] **Step 2: Write failing URL and document tests**

Create `tests/test_site_check.py` with standard-library `unittest` cases proving that:

- `collect_html_routes()` converts `index.html` to `/` and nested files to `/path/file.html`.
- `validate_expected_routes()` reports a missing legacy route.
- `validate_html_document()` reports zero H1 elements, more than one H1, images without alt text, links without accessible text, and pages without `main`.

- [ ] **Step 3: Run the tests and confirm failure**

Run: `python -m unittest discover -s tests -p "test_*.py" -v`

Expected: FAIL because `scripts.site_check` does not exist.

- [ ] **Step 4: Implement the validation harness**

Implement the three functions with `pathlib` and `html.parser`. The CLI prints one error per line and exits 1 on any error. It ignores decorative images only when they have `alt=""` and `aria-hidden="true"`.

- [ ] **Step 5: Run unit and baseline checks**

Run:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
hugo --minify --panicOnWarning --printPathWarnings
python scripts/site_check.py --public public --expected tests/expected-urls.txt
```

Expected: unit tests PASS; Hugo exits 0; the compatibility check reports no missing routes. Structural findings against the legacy theme may be recorded as an explicit temporary allowlist that Task 2 removes.

- [ ] **Step 6: Separate build and deployment permissions**

Update `.github/workflows/gh-pages.yml` to pin Hugo Extended 0.145.0, checkout without submodules, run unit tests and the Hugo build in a read-only build job, and upload the generated `public/` directory as a workflow artifact. A separate `master`-only job downloads that artifact and publishes it to the existing `gh-pages` branch with `contents: write`. Pull requests must never receive write permission. This preserves the repository's current Pages source and avoids a settings migration.

- [ ] **Step 7: Verify workflow syntax and commit**

Run `hugo --minify --panicOnWarning --printPathWarnings` and the Python checks again.

Commit:

```bash
git add .github/workflows/gh-pages.yml hugo.toml scripts/site_check.py tests
git commit -m "build: add reproducible site validation"
```

### Task 2: Replace Wowchemy with an accessible local site shell

**Files:**
- Create: `layouts/_default/baseof.html`
- Create: `layouts/_default/single.html`
- Create: `layouts/_default/list.html`
- Create: `layouts/partials/head.html`
- Create: `layouts/partials/header.html`
- Create: `layouts/partials/footer.html`
- Create: `layouts/partials/seo.html`
- Create: `layouts/404.html`
- Create: `assets/css/main.css`
- Create: `assets/js/navigation.js`
- Modify: `hugo.toml`
- Modify: `config/_default/config.yaml`
- Modify: `config/_default/menus.yaml`
- Test: `tests/test_site_check.py`

**Interfaces:**
- Consumes: `.Site.Menus.main`, `.Site.Params`, `.Title`, `.Description`, and page `.Content`
- Produces: semantic HTML shell with `header`, `nav`, `main`, and `footer`
- Produces: CSS tokens `--canvas`, `--surface`, `--ink`, `--muted`, `--signal`, `--line`, and spacing/type scales
- Produces: optional mobile navigation initialized from `[data-nav-toggle]` and `[data-nav-menu]`

- [ ] **Step 1: Add failing shell assertions**

Extend `tests/test_site_check.py` so a representative page fails unless it has exactly one H1, a skip link targeting `#main-content`, labelled primary navigation, a `main` element, accessible social-link names, canonical metadata, a description, and keyboard-focus CSS linked from the page.

- [ ] **Step 2: Run the failing checks against the legacy output**

Run: `python scripts/site_check.py --public public --expected tests/expected-urls.txt`

Expected: FAIL on the legacy H1, skip-link, social-link, and landmark requirements.

- [ ] **Step 3: Implement the local templates**

Create the local base, list, single, header, footer, head, SEO, and 404 templates. The header exposes the name as a home link, renders the main menu, and uses a real button for the mobile menu. The search modal and display-preference controls are removed.

- [ ] **Step 4: Implement the visual foundation**

Create a light-first editorial system in `assets/css/main.css` using local/system typefaces and these initial tokens:

- `--canvas: #f6f8fc`
- `--surface: #ffffff`
- `--ink: #14213d`
- `--muted: #58657a`
- `--signal: #2556d8`
- `--line: #d8e0ee`

Keep body text left aligned with a maximum readable width of 72 characters. Use a restrained routing-line motif only in the homepage hero and research-theme navigation. Add clear `:focus-visible`, 360px mobile behavior, print styles, and `prefers-reduced-motion` handling.

- [ ] **Step 5: Remove theme dependencies from active configuration**

Remove the active theme and Wowchemy module imports from `hugo.toml` and `config/_default/config.yaml`. Preserve `baseURL`, `relativeURLs`, `uglyURLs`, and existing permalinks. Do not delete legacy files yet.

- [ ] **Step 6: Build, validate, and inspect**

Run the unit tests, Hugo build, and site checker. Serve `public/` locally and inspect Home, Publications, one publication, and 404 at 360x800 and 1440x900. Confirm that focus remains visible and the mobile menu works with keyboard input.

- [ ] **Step 7: Commit**

```bash
git add hugo.toml config/_default layouts assets/css/main.css assets/js/navigation.js tests/test_site_check.py
git commit -m "feat: add local accessible Hugo shell"
```

### Task 3: Normalize publications and add the 2025-2026 research record

**Files:**
- Create: `layouts/publications/list.html`
- Create: `layouts/publications/single.html`
- Create: `layouts/partials/publication-card.html`
- Create: `archetypes/publications.md`
- Modify: `content/publications/*/index.md`
- Create: `content/publications/2026-critique-guided-distillation/index.md`
- Create: `content/publications/2026-load-balancing-expert-pruning/index.md`
- Create: `content/publications/2025-spear-mm/index.md`
- Create or verify: records for CoT-Guard, model-diversity reasoning, Structured Thoughts, and prompt-difficulty prediction
- Modify: `tests/test_site_check.py`

**Interfaces:**
- Consumes front matter: `title`, `date`, `slug`, `authors`, `venue.name`, `venue.type`, `status`, `links`, `topics`, `featured`, `featured_weight`, `summary`, and `contribution`
- Produces publication cards and detailed publication pages
- Produces `data-status` and `data-topic` attributes for progressive filtering without making JavaScript necessary for access

- [ ] **Step 1: Add failing publication assertions**

Add tests that fail when generated publication pages contain `Unknown Journal`, an ellipsis-truncated abstract, generic link text such as `Link`, a missing status, duplicate canonical URLs, or Markdown markup inside rendered author names. Add a homepage-order fixture expecting CGD, expert pruning, and SPEAR-MM in that order.

- [ ] **Step 2: Add build-time required-field validation**

In `publication-card.html` and `publications/single.html`, use Hugo `errorf` calls when title, date, authors, venue name, venue type, status, summary, or contribution is missing. Optional links must be omitted cleanly rather than rendered empty.

- [ ] **Step 3: Verify current content fails the new contract**

Run: `hugo --minify --panicOnWarning --printPathWarnings`

Expected: FAIL on existing incomplete publication metadata.

- [ ] **Step 4: Curate the existing publication records**

Normalize all 14 existing records. Resolve duplicate entries, author disagreements, year disagreements, and malformed venues against canonical journal or proceedings pages. Preserve each existing public route by keeping its current slug or adding an alias that generates the same `.html` path.

- [ ] **Step 5: Add and verify the new research records**

Create records for:

1. Critique-Guided Distillation for Robust Reasoning via Refinement - PMLR/ICML 2026, published proceedings, `featured_weight: 1`.
2. When Load-Balancing Goes Too Far: Expert Pruning in Over-Dispersed Mixture-of-Experts Models - accepted to the NeurIPS 2026 Workshop on On-Device Intelligence, `featured_weight: 2`.
3. SPEAR-MM - IEEE Big Data 2025, `featured_weight: 3`.
4. CoT-Guard - add only after verifying its exact NeurIPS 2026 track and canonical link.
5. Your Model Diversity, Not Method, Determines Reasoning Strategy - label as the ICLR 2026 logical-reasoning workshop unless a main-track source proves otherwise.
6. Structured Thoughts for Improved Reasoning and Context Pruning - label as preprint or under review until a canonical acceptance source exists.
7. Optimizing Reasoning Efficiency through Prompt Difficulty Prediction - label with the exact NeurIPS Efficient Reasoning workshop name.

Use first-party proceedings, conference, journal, DOI, arXiv, or OpenReview pages for every link. Do not infer acceptance from résumé wording alone.

- [ ] **Step 6: Build and verify the publication experience**

Run the full Hugo build and Python checks. Inspect long author lists and titles at 360px and verify no horizontal scrolling. Confirm CGD renders first in featured research regardless of publication date.

- [ ] **Step 7: Commit**

```bash
git add layouts/publications layouts/partials/publication-card.html archetypes/publications.md content/publications tests/test_site_check.py
git commit -m "content: curate and expand publication record"
```

### Task 4: Build the research-led homepage

**Files:**
- Create: `data/profile.yaml`
- Create: `content/_index.md`
- Create: `layouts/index.html`
- Create: `layouts/partials/focus-area.html`
- Modify: `assets/css/main.css`
- Test: `tests/test_site_check.py`

**Interfaces:**
- Consumes: `.Site.Data.profile`, featured publication pages, and homepage Markdown
- Produces: hero, proof, focus areas, featured research, career arc, and contact CTA

- [ ] **Step 1: Add failing homepage tests**

Assert that generated `/index.html` contains:

- One H1 with `I lead research and engineering for efficient, reliable language models.`
- The exact current title.
- Links to Publications, CV, Google Scholar, GitHub, LinkedIn, and email.
- Three focus areas.
- Exactly three featured publication cards in the approved order.
- No phone number, ZIP code, `Personal page`, or generic `cutting-edge` copy.

- [ ] **Step 2: Run the failing test**

Run the Hugo build and site checker.

Expected: FAIL because the new homepage has not been implemented.

- [ ] **Step 3: Create the public-safe profile data**

Add name, official title, short bio, email, professional links, research themes, and proof points to `data/profile.yaml`. Use only public research evidence in the initial version. Keep internal scale and performance metrics out of the file.

- [ ] **Step 4: Implement the homepage**

Build the hero and sections specified in the design. Treat typography as the main visual identity. Use one restrained routing-line element to connect the three focus areas. The primary CTA is `Explore the research`; secondary actions are `Read the CV` and `Get in touch`.

- [ ] **Step 5: Verify content, accessibility, and responsive layout**

Run all automated checks. Inspect at 360px, 768px, and 1440px. Confirm that the portrait does not delay the positioning statement on mobile and that the featured-order test passes.

- [ ] **Step 6: Commit**

```bash
git add data/profile.yaml content/_index.md layouts/index.html layouts/partials/focus-area.html assets/css/main.css tests/test_site_check.py
git commit -m "feat: launch research-led homepage"
```

### Task 5: Add Research, Leadership, About, and Research Notes

**Files:**
- Create: `content/research/_index.md`
- Create: `content/research/reasoning-and-distillation.md`
- Create: `content/research/efficient-model-systems.md`
- Create: `content/research/trustworthy-ml.md`
- Create: `content/leadership/_index.md`
- Create: `content/about/_index.md`
- Create: `content/writing/_index.md`
- Create: `layouts/research/list.html`
- Create: `layouts/leadership/list.html`
- Create: `layouts/writing/list.html`
- Modify: `config/_default/menus.yaml`
- Modify: `assets/css/main.css`
- Test: `tests/test_site_check.py`

**Interfaces:**
- Consumes: Markdown front matter and `data/profile.yaml`
- Produces: `/research.html`, `/leadership.html`, `/about.html`, and `/writing.html`

- [ ] **Step 1: Add failing section-page tests**

Assert unique titles and descriptions, one H1, correct menu labels, no confidential claims, and at least one relevant publication link from each research theme. Assert that the About page maps Delft to Applied Mathematics and Erlangen-Nuremberg to Computational Engineering.

- [ ] **Step 2: Run checks and confirm missing-page failures**

Run the Hugo build and site checker.

Expected: FAIL because the new section pages and menu entries are absent.

- [ ] **Step 3: Write the research pages**

Explain each research area in plain language, state Berkcan's contribution, and link to the strongest supporting papers. Do not duplicate full publication abstracts.

- [ ] **Step 4: Write the leadership and About pages**

Frame leadership through technical ownership, research direction, release standards, and cross-team adoption. Use a concise career arc. Exclude the résumé phone number, ZIP code, employer-confidential details, and unapproved internal metrics.

- [ ] **Step 5: Add the Research Notes landing page without filler posts**

Publish an honest empty state that lists the intended themes and links readers to current research. Do not manufacture dated posts merely to populate the page.

- [ ] **Step 6: Build, inspect, and commit**

Run all automated checks and inspect the four pages at mobile and desktop sizes.

```bash
git add content/research content/leadership content/about content/writing layouts/research layouts/leadership layouts/writing config/_default/menus.yaml assets/css/main.css tests/test_site_check.py
git commit -m "content: add research and leadership narrative"
```

### Task 6: Add SEO, structured data, and automated accessibility checks

**Files:**
- Modify: `layouts/partials/seo.html`
- Create: `layouts/partials/schema-person.html`
- Create: `layouts/partials/schema-publication.html`
- Create: `package.json`
- Create: `package-lock.json`
- Create: `.pa11yci.json`
- Modify: `.github/workflows/gh-pages.yml`
- Modify: `tests/test_site_check.py`

**Interfaces:**
- Produces: Person JSON-LD on the homepage
- Produces: ScholarlyArticle JSON-LD on complete publication pages
- Produces: `npm run check:a11y` against locally served generated pages

- [ ] **Step 1: Add failing metadata tests**

Assert that every indexed page has a unique title, non-generic description, canonical URL, Open Graph title/description, and no more than one JSON-LD block of each supported type. Assert the homepage Person object names Berkcan and publication objects contain headline, authors, datePublished, and URL.

- [ ] **Step 2: Run tests and confirm metadata failures**

Run the Hugo build and Python test suite.

Expected: FAIL until the structured-data partials are wired into the head.

- [ ] **Step 3: Implement structured metadata**

Generate escaped JSON with Hugo's JSON encoding rather than hand-built string concatenation. Do not emit ScholarlyArticle markup when required fields are missing.

- [ ] **Step 4: Add Pa11y CI**

Pin Pa11y CI and a static HTTP server in `package-lock.json`. Configure checks for Home, Research, Publications, one long-author publication, Leadership, About, and 404 at desktop and mobile widths. Fail on WCAG2AA errors. The production build itself must remain Hugo-only.

- [ ] **Step 5: Integrate accessibility checks into pull requests**

Update the build job to run `npm ci`, serve `public/`, execute `npm run check:a11y`, and stop the server. Keep deploy permissions isolated.

- [ ] **Step 6: Run and commit**

Run Python tests, the Hugo build, and Pa11y. Expected: all checks exit 0 with no serious accessibility findings.

```bash
git add layouts/partials/seo.html layouts/partials/schema-person.html layouts/partials/schema-publication.html package.json package-lock.json .pa11yci.json .github/workflows/gh-pages.yml tests/test_site_check.py
git commit -m "feat: add search and accessibility metadata"
```

### Task 7: Remove legacy machinery and document owner maintenance

**Files:**
- Remove: `themes/matteo-custom/`
- Remove: `themes/starter-hugo-academic/`
- Remove: `themes/github.com/wowchemy/`
- Remove: `content/admin/`
- Remove: `content/home/`
- Remove: obsolete `content/news/` and blank `content/gallery/`
- Remove: `.gitmodules`
- Remove: `.submodule/scholar-collector`
- Remove: `update-publications.sh`
- Remove: unused copied layouts, jQuery, code-folding, R Markdown, gallery, font, and theme assets
- Modify: `README.md`
- Modify: `tests/expected-urls.txt`
- Modify: `tests/test_site_check.py`

**Interfaces:**
- Consumes: the local renderer and normalized content from Tasks 2-6
- Produces: one documented owner workflow with no active theme, CMS, or submodule dependency

- [ ] **Step 1: Add cleanup-regression tests**

Add assertions that generated HTML contains no Netlify Identity, Wowchemy, jQuery, unused code-folding assets, blank gallery links, or hidden social links. Assert every route in the compatibility fixture still exists.

- [ ] **Step 2: Verify the tests fail before cleanup**

Run the Hugo build and site checker.

Expected: FAIL because legacy assets and generated integrations are still present.

- [ ] **Step 3: Remove legacy dependencies**

Delete the replaced theme trees, CMS content, Scholar submodule, updater script, copied legacy partials, obsolete JavaScript, and unused content. Before each directory removal, confirm its exact repository-relative path and confirm the local renderer no longer references it.

- [ ] **Step 4: Preserve intentional legacy routes**

For removed content that had meaningful public URLs, add minimal aliases or redirect pages. Do not preserve blank gallery and admin pages in the sitemap.

- [ ] **Step 5: Write the owner README**

Document prerequisites, Hugo 0.145.0 installation, local preview, content locations, publication archetype fields, featured ordering, research-note creation, CV replacement, validation commands, pull-request review, merge, deployment verification, and rollback.

State clearly that the repository stores the public PDF, not the résumé source containing phone and ZIP details. Explain that the current PDF must not be replaced until the updated source compiles and the PDF is visually reviewed.

- [ ] **Step 6: Run the full local quality gate**

Run:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
hugo --minify --panicOnWarning --printPathWarnings
python scripts/site_check.py --public public --expected tests/expected-urls.txt
npm ci
npm run check:a11y
```

Expected: all commands exit 0; no missing intended legacy URL, console error, ambiguous publication status, structural accessibility error, or generic metadata remains.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor: remove legacy academic theme stack"
```

### Task 8: Final visual, content, and deployment verification

**Files:**
- Modify only files required by issues found during this task
- Create: `docs/release/research-led-site-checklist.md`

**Interfaces:**
- Consumes: completed site and all validation commands
- Produces: signed-off release checklist and deployable branch

- [ ] **Step 1: Verify the repository state**

Run `git status --short`, review the branch diff against the pre-redesign commit, and confirm that no secret, phone number, ZIP code, generated `public/` directory, or local build artifact is tracked.

- [ ] **Step 2: Run the complete quality gate from a clean build**

Remove only the generated `public/` directory after verifying the resolved path is inside the repository, rebuild from scratch, and run every command from Task 7 Step 6.

- [ ] **Step 3: Perform browser acceptance checks**

Inspect Home, Research, Publications, the three featured papers, Leadership, About, Research Notes, 404, sitemap, and CV link. Test 360x800, 768x1024, and 1440x900; keyboard-only navigation; reduced motion; long author lists; broken external links; and social-preview metadata.

- [ ] **Step 4: Verify all claims against sources**

Compare every current title, author list, year, venue, status, and quantitative result with a primary source. Remove any claim that cannot be verified or approved for public use.

- [ ] **Step 5: Record the release checklist**

Create `docs/release/research-led-site-checklist.md` with the commands run, their exit status, URLs reviewed, known limitations, and confirmation that CGD is featured first.

- [ ] **Step 6: Request whole-branch review and fix findings**

Have a fresh reviewer compare the branch against the approved spec and this plan. Fix blocking findings and rerun the relevant checks.

- [ ] **Step 7: Commit release verification**

```bash
git add docs/release/research-led-site-checklist.md
git commit -m "docs: record portfolio release verification"
```

- [ ] **Step 8: Publish through a reviewable branch**

Push the feature branch, open a pull request, confirm the read-only build and accessibility checks pass, review the generated Pages artifact, and merge only after the user approves the final visual result. Confirm the production GitHub Pages deployment succeeds after merge.
