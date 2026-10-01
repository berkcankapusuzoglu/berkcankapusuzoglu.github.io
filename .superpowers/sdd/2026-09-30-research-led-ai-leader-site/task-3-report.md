# Task 3 report — curated publication record

## Changes

- Added Hugo publication list/detail templates, publication card/link/validation partials, and a publication archetype.
- Normalized all 14 legacy records to include plain author names, venue name/type, status, descriptive primary-source link, topic, complete summary field, and contribution.
- Added records for CGD, expert pruning, SPEAR-MM, model-diversity reasoning, Structured Thoughts, and prompt-difficulty prediction. Added explicit featured weights 1, 2, and 3 to CGD, expert pruning, and SPEAR-MM.
- Kept the previously generated publication routes unchanged and added the six new routes to `tests/expected-urls.txt`.
- Added wrap-safe publication styles and generated-output assertions for metadata, resource links, source URL uniqueness, feature weights, and long text.
- Recorded primary source links and evidence notes in `docs/research/publication-sources.md`.

## Primary sources used

Primary sources are linked per-record in the source ledger. Key sources include PMLR for CGD and StructMoE; arXiv for expert pruning, SPEAR-MM, model-diversity reasoning, Structured Thoughts, and prompt-difficulty prediction; OpenReview workshop PDFs for model-diversity and prompt-difficulty papers; publisher records from Springer, ASME, ScienceDirect, AIAA, PHM Society, and NIST for legacy publications; IEEE DOI `10.1109/BigData66926.2025.11402347` for SPEAR-MM's conference publication.

## Evidence gaps and conservative decisions

- Expert pruning is labeled `preprint` because its arXiv record was found but workshop acceptance was not publicly verifiable from a primary source.
- CoT-Guard is omitted because its public arXiv record does not verify a NeurIPS track or acceptance.
- CGD uses the exact PMLR title, ordered authors (including Zain Sarwar), PMLR volume 306, and published status.
- SPEAR-MM is listed as published at IEEE Big Data 2025 using the IEEE DOI as its canonical resource.
- Some older imported abstracts were already truncated. Their rendered summaries no longer display an ellipsis, but several are excerpted at the source text's original cutoff; this remains a content review item. Some older submission metadata, especially exact display-name/date details for AIAA records, merits a follow-up verification against publisher metadata.

## Validation outcomes

- `python -m unittest discover -s tests -p "test_*.py" -v` — PASS, 42 tests.
- `hugo --minify --panicOnWarning --printPathWarnings` — PASS, Hugo 0.145.0 Extended; 51 pages, 8 aliases.
- `python scripts/site_check.py --public public --expected tests/expected-urls.txt` — PASS.
- Exact route comparison — PASS: 47 actual routes, 47 expected routes, no missing or unexpected routes. All baseline routes remain present.
- Browser inspection at 360×800 and 1440×900 — PASS, no horizontal overflow on the publications list, CGD, expert-pruning, SPEAR-MM, or the long-author StructMoE publication page. The list displayed CGD first among the three featured cards by date; explicit featured weights are present for the homepage selector.
- `git diff --check` — PASS.

## Self-review, deviations, and risks

- Required-field Hugo errors were observed before normalizing legacy records, then resolved by adding the missing canonical fields.
- The test for featured weight order checks both the three explicit per-record weights and the production selector's use of `Params.featured_weight`. Homepage composition belongs to Task 4 and was not modified here.
- The browser viewport was reset after inspection. No production site or external service was changed.
- Task 3 implementation commit SHA: `f242133514fdf3f7ef7154f8811160be3c4fd0ac` (`content: curate and expand publication record`).
