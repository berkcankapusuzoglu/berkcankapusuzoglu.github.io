# Tasks 6–7 implementation report

## Task 6 — SEO, structured data, and accessibility

Commit: `2c076cf34cf9ad71c05e07f4276f094874a6e2b9` (`feat: add search and accessibility metadata`).

Added unique SEO titles/descriptions, canonical and Open Graph metadata, safely JSON-encoded `Person` and `ScholarlyArticle` structured data, and pinned Pa11y CI tooling. CI runs the accessibility audit separately from the Hugo-only production build. The homepage carry-forward notes were resolved: its proof strip now uses publication-backed facts, the research CTA targets `/research.html`, and About identifies the Ph.D. field as Civil Engineering.

Generated-output tests were added first and failed for missing metadata/schema before the corresponding partials were implemented. Pa11y's server lifecycle was exercised locally and its runner starts and stops the static server.

## Task 7 — maintenance workflow and legacy isolation

Commit: this report is included in the Task 7 commit; the exact SHA is reported in the task handoff (and is available with `git rev-parse HEAD`).

The owner README now documents Hugo 0.145.0 installation, local preview, content locations, publication fields and feature weights, the Research Notes-to-LinkedIn workflow, safe CV replacement, validation commands, and review/deployment/rollback.

Regression coverage confirms that generated HTML has no active Netlify Identity, Wowchemy, jQuery, code-folding, or legacy-theme/submodule references; gallery links and hidden professional social links are absent. Admin and blank gallery routes are intentionally retired. Meaningful news URLs are retained as noindex redirects: `/news.html` → `/writing.html`, `/news/job/job.html` → `/about.html`, and `/news/personal/personal.html` → `/research/efficient-model-systems.html`. News pagination and obsolete `job`/`personal` tag routes were removed from the expected route fixture. The author bundle retains and publishes the portrait at `authors/admin/avatar.jpg`.

### Physical cleanup limitation and follow-up

The requested physical deletion was blocked by the approvals reviewer because the recursive removal had broad, irreversible scope and could remove meaningful public content. No alternate deletion mechanism was attempted. Legacy files remain physically present and dormant/unreferenced by the active site. This is not a full physical theme-stack cleanup.

Exact top-level paths still requiring a separately approved cleanup are:

- `themes/matteo-custom/`
- `themes/starter-hugo-academic/`
- `themes/github.com/wowchemy/`
- `content/admin/`
- `content/home/`
- `content/news/`
- `content/gallery/`
- `.gitmodules`
- `.submodule/scholar-collector/`
- `update-publications.sh`
- unused copied legacy layouts, assets, and scripts identified by the reference scan

The content ignore rules suppress retired admin/home/gallery/news source routes without deleting their source. The preserved CV PDF remains at `static/files/resume/Berkcan_Resume.pdf`. Hugo still copies unreferenced files from `static/`; the regression guarantee is that legacy assets are not referenced by generated HTML, not that their bytes are absent from the output.

## Verification

Task 6 and Task 7 were verified from clean generated destinations. Final Task 7 results:

- `python -m unittest discover -s tests -p "test_*.py" -v` — PASS, 66 tests.
- `hugo --minify --panicOnWarning --printPathWarnings --destination public` after removing the exact `public/` destination — PASS, 46 pages, 6 paginator pages, 13 static files, 11 aliases.
- `python scripts/site_check.py --public public --expected tests/expected-urls.txt` — PASS.
- `npm ci` — PASS using the pinned lockfile; `npm audit` — PASS, 0 vulnerabilities.
- `npm run check:a11y` — PASS, 16/16 desktop/mobile URL checks, 0 Pa11y errors.
- `node --check scripts/check_a11y.mjs` — PASS.
- `git diff --check` — PASS.

Pa11y emitted a dependency deprecation warning but no accessibility errors. No deploy or push was performed.

## Self-review

The generated route fixture and redirects explicitly encode the intentional public URL decisions; normalized publications and their sources are unchanged. Legacy directory deletion remains outstanding and must not be described as complete. Task 7 is a safe isolation/documentation step only.

## Review remediation

The combined review found four issues after the Task 7 commit. They are addressed in a focused follow-up commit, `fix: correct metadata and research notes publishing` (exact commit SHA is in the final handoff).

- ScholarlyArticle JSON-LD now uses `sameAs` for DOI/proceedings/arXiv resource URLs. Status remains visible in publication HTML and is omitted from schema. `isPartOf` is a `Periodical` for journals, a `CreativeWorkSeries` for proceedings, and absent for arXiv preprints. Generated JSON-LD contract tests cover CGD, expert-pruning preprint, and a journal.
- The SEO partial no longer reads `.Paginator` or manually applies `htmlEscape`. Pagination metadata is passed only for section/taxonomy/term contexts from the base layout. Accidental root and 404 page-2/page-3 duplicates are absent; route tests assert that. The exact generated HTML route fixture contains 48 routes, including only intentional list pagination outputs.
- Research Notes now lists child page bundles with linked title, date, and summary; the empty-state content appears only when no notes exist. A Hugo fixture test adds a temporary note bundle and verifies its generated output without creating a public post. README instructions now use `content/writing/<slug>/index.md`.
- Home metadata relies on Go template contextual escaping. Generated metadata tests decode the attribute and verify the apostrophe is correct.

Final remediation gate:

- `python -m unittest discover -s tests -p "test_*.py" -v` — PASS, 71 tests.
- Clean `hugo --minify --panicOnWarning --printPathWarnings --destination public` — PASS, 46 pages, 2 paginator pages, 13 static files, 9 aliases; 48 generated HTML routes.
- `python scripts/site_check.py --public public --expected tests/expected-urls.txt` — PASS, exact route contract.
- `npm ci` — PASS using the lockfile; `npm audit` — PASS, 0 vulnerabilities.
- `npm run check:a11y` — PASS, 16/16 desktop/mobile URL checks, 0 errors.
- `node --check scripts/check_a11y.mjs` and `git diff --check` — PASS.

The first npm install attempt was denied network access and exited with an npm internal error; after network permission was granted, the pinned install and all Node checks passed. Pa11y emitted only the dependency deprecation warning. Legacy physical cleanup remains blocked as documented above.
