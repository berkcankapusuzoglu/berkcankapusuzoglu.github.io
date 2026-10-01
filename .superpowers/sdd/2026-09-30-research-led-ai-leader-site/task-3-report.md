# Task 3 report — curated publication record

## Changes

- Added Hugo publication list/detail templates, publication card/link/validation partials, and a publication archetype.
- Normalized all 14 legacy records to include plain author names, venue name/type, status, descriptive primary-source link, topic, complete summary, and distinct contribution. Restored the legacy publication-type taxonomy term.
- Added records for CGD, expert pruning, SPEAR-MM, model-diversity reasoning, Structured Thoughts, and prompt-difficulty prediction. Added explicit featured weights 1, 2, and 3 to CGD, expert pruning, and SPEAR-MM.
- Kept the full legacy route contract unchanged, including taxonomy and pagination routes, and added the six new publication routes to `tests/expected-urls.txt`.
- Added wrap-safe publication styles and generated-output assertions for metadata, resource links, source URL uniqueness, feature weights, and long text.
- Recorded primary source links and evidence notes in `docs/research/publication-sources.md`.

## Primary sources used

Primary sources are linked per-record in the source ledger. Key sources include PMLR for CGD and StructMoE; arXiv for expert pruning, SPEAR-MM, model-diversity reasoning, Structured Thoughts, and prompt-difficulty prediction; OpenReview workshop PDFs for model-diversity and prompt-difficulty papers; publisher records from Springer, ASME, ScienceDirect, AIAA, PHM Society, and NIST for legacy publications; IEEE DOI `10.1109/BigData66926.2025.11402347` for SPEAR-MM's conference publication.

## Evidence gaps and conservative decisions

- Expert pruning is labeled `preprint` because its arXiv record was found but workshop acceptance was not publicly verifiable from a primary source.
- CoT-Guard is omitted because its public arXiv record does not verify a NeurIPS track or acceptance.
- CGD uses the exact PMLR title, ordered authors (including Zain Sarwar), PMLR volume 306, and published status.
- SPEAR-MM is listed as published at IEEE Big Data 2025 using the IEEE DOI as its canonical resource.
- Some older submission metadata, especially exact display-name/date details for AIAA records, merits a follow-up verification against publisher metadata.

## Validation outcomes

- `python -m unittest discover -s tests -p "test_*.py" -v` — PASS, 45 tests, including a Hugo build into a newly created `TemporaryDirectory` and exact route equality.
- Fresh empty destination: `hugo --minify --panicOnWarning --printPathWarnings --destination .tmp-publication-build` — PASS, Hugo 0.145.0 Extended; 53 pages, 2 paginator pages, 9 aliases.
- `python scripts/site_check.py --public .tmp-publication-build --expected tests/expected-urls.txt` — PASS against the fresh destination.
- Exact fresh route comparison — PASS: 47 actual routes, 47 expected routes, no missing or unexpected routes. This includes `/publication-type/2.html`, its page 1 and page 2 routes, and `/publications/page/2.html`.
- Normal strict build and `python scripts/site_check.py --public public --expected tests/expected-urls.txt` — PASS.
- Browser viewport recheck for this review follow-up — attempted, but unavailable: the computer-use browser inventory returned no browsers in the subagent session. The prior Task 3 report contains the earlier 360×800 and 1440×900 inspection; no new visual claim is made for the corrective commit.
- `git diff --check` — PASS.

## Self-review, deviations, and risks

- The prior route result came from stale `public/`; this follow-up now guards against that with a fresh temporary destination and exact equality assertion.
- Legacy route preservation uses original `publication_types: ["2"]` metadata and 10-item pagination. The duplicate Witherell route is retained as a canonical-record link and does not appear in the publication list.
- Featured-order coverage reads the three production records' `featured` flags and explicit weights, sorts by those weights, and asserts the selector uses `Params.featured_weight`. The generated homepage-order assertion is owned by Task 4; the homepage was not changed here.
- `git diff --check` — PASS; no whitespace errors.
- The browser viewport was reset after inspection. No production site or external service was changed.
- Task 3 implementation commit SHA: `f242133514fdf3f7ef7154f8811160be3c4fd0ac` (`content: curate and expand publication record`).
- Task 3 review-fix commit SHA: `71fab927d785d5d6f8c91317d2ba3185a8ac36a4` (`fix: preserve publication routes and content quality`).
