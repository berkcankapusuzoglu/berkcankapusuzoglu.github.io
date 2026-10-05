# Adding a paper visual

Add one reviewed figure to a publication page bundle. The five-minute path below assumes its rights, source and scientific meaning have already been checked. Run commands from the repository root in PowerShell.

## Before preparing a figure

Use [visual-inventory.yaml](visual-inventory.yaml) and [the Release 2 backlog](visual-release-2.md) to select the exact nested project and entry. For pending candidates, record a specific license or permission, evidence URL, scope, reviewer and date before import. `rights-review-required` is a closed gate. The CLI does not enforce this editorial gate. Compare the figure, number and caption with the final paper, then record the source page and intended output. Archive access or authorship alone does not establish reuse rights.

You need Hugo Extended 0.145.0, Python 3.13 with Pillow, and Poppler's `pdftoppm` on `PATH`. On this Windows workspace, the bundled interpreter already has Pillow:

```powershell
$assetPython = 'C:\Users\berkc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$archive = 'C:\Users\berkc\Desktop\Overleaf Projects (12 items).zip'
& $assetPython -c "from PIL import Image; print(Image.__version__)"
hugo version
pdftoppm -v
```

On another machine, point `$assetPython` to a Python 3.13 interpreter with Pillow and `$archive` to the private outer ZIP. Inventory and extraction need no Pillow; preparation, sequence authoring and the full asset tests do. Keep ZIPs outside the repository. `research-source/` and `asset-work/` are ignored scratch directories, not publication destinations.

## Five-minute path for an approved source

1. Preview the archive without unpacking it:

   ```powershell
   & $assetPython scripts/research_assets.py inventory --archive $archive
   ```

   Output is deterministic JSON (also a YAML 1.2 subset), including project/figure counts, paths, sizes and SHA-256 checksums. The current archive contains 12 projects and 234 figures. Copy the exact case-sensitive project and entry names.

2. Prepare one named PDF page. This example uses an approved CGD entry and a new output name, so it cannot overwrite the current lead image:

   ```powershell
   & $assetPython scripts/research_assets.py prepare --archive $archive --project '[ICML_2026] CGD.zip' --entry 'figures/cgd_overview.pdf' --output 'content/publications/2026-critique-guided-distillation/media/cgd-overview-review.png' --dpi 180 --page 1
   ```

   Change the bundle and names to your approved selection. Output must be a PNG inside this repository's `content/publications/` tree. DPI accepts 72–600; page is one-based and defaults to 1. Temporary PDF/raster files are removed automatically. Existing outputs fail unless you deliberately add `--replace`; prefer a new filename while reviewing. Save the emitted archive/source/output checksums, page, DPI, dimensions and bytes in the manifest, together with the original caption, public caption, paper URL, figure number and reuse evidence. Mark the entry approved only after review.

   To inspect an exact source file separately, extract only that entry to ignored scratch space:

   ```powershell
   & $assetPython scripts/research_assets.py extract --archive $archive --project '[ICML_2026] CGD.zip' --entry 'figures/cgd_overview.pdf' --output 'asset-work/cgd-overview-review.pdf'
   ```

   `extract` writes the explicit destination and can overwrite it; choose a fresh scratch name. It does not convert the PDF or enforce the publication-directory restriction. Never extract a whole project into Git.

3. Add an entry under `visuals` in the bundle's `index.md`:

   ```yaml
   visuals:
     - id: method-overview
       file: media/cgd-overview-review.png
       role: lead
       alt: "Describe the diagram's stages and relationships."
       caption: "State what this figure shows and its evaluated setting."
       takeaway: "One supported insight the reader should remember."
       source_label: "Author et al. (year), Figure 1"
       source_url: "https://example.org/canonical-paper"
       license: "Specific verified license or permission"
       homepage: false
   ```

   Replace all placeholder prose and URLs. `file` is relative to `index.md`, not the repository root; use an exact local resource path. Required fields are shown above except `homepage`, which is optional. IDs must be unique on the page; roles are `lead`, `result` or `supporting`. Publication figures render in metadata order. Missing fields/resources, duplicate IDs and remote files fail the build. The validator checks presence, not factual accuracy or permission evidence.

   Usually update an existing entry rather than append a duplicate lead figure. Keep CGD as the sole `homepage: true` visual and keep featured order CGD, expert pruning, SPEAR-MM. Publication title, date, authors, venue, status, summary and contribution remain required; see [the archetype](../../archetypes/publications.md). Templates require `topics` and `links` lists; release tests expect a published paper to have a topic and a canonical paper link. If creating a new publication, add its generated `.html` route to `tests/expected-urls.txt` and stage that file too. Existing visual updates do not add routes.

4. Preview and inspect the updated route:

   ```powershell
   hugo server
   ```

   Open the address printed by Hugo and follow the publication link. Existing publication URLs end in `.html`. Inspect at 360×800 and 1440×900, then stop the server with Ctrl+C before running checks.

5. Run [the README validation commands](../../README.md#validate-changes), using `& $assetPython` in place of `python`. Start with the Python suite, production Hugo build and HTML checker; run the JavaScript syntax and Pa11y checks before release. Node.js 22+ is needed only for those accessibility tools. `npm ci` installs the pinned dependencies.

6. Review the diff and commit only the intended files:

   ```powershell
   git status --short
   git diff --check
   git add content/publications/2026-critique-guided-distillation/index.md content/publications/2026-critique-guided-distillation/media/cgd-overview-review.png docs/research/visual-inventory.yaml
   git commit -m "content: update reviewed paper visual"
   ```

   Adjust the exact staged paths to your update. Review the local companion preview before pushing this visual-library release. Once approved, push your feature branch and open a PR against `master`; merge after checks and artifact review. A push to `master` builds and deploys to `gh-pages`. Confirm the live page after deployment. Roll back through a reviewed `git revert <offending-commit>` on a branch and merge that PR; use `git revert -m 1 <merge-commit>` when reverting a merge. Do not edit generated `public/` files or reset shared history. See [review and deployment](../../README.md#review-and-deployment).

## Editing and verification gates

You can refine alt text, captions, takeaways and adjacent explanation within the verified paper's scope. You can choose visual order and a clearer filename, provided metadata and resources stay in sync. Keep ID changes deliberate because they change figure anchors.

Verify numerical claims, benchmarks, experimental settings, author order, venue/status and citation changes against the paper or acceptance evidence. Record precise workshop names; acceptance at the NeurIPS 2026 Workshop on On-Device Intelligence must not imply main-track acceptance. License, permission scope, source URL, figure identity and scientific edits require evidence before publication. Homepage selection and featured order are release decisions, not routine copy edits.

## Quality, accessibility and confidentiality checklist

- Compare the full PNG to the source: retain axes, legends, units, confidence intervals, labels and scientific meaning. Only remove excess whitespace after review; the preparation command does not crop.
- Read every label at desktop and mobile widths. Dense featured figures may scroll sideways; confirm keyboard focus and scrolling reveal the whole figure. Add nearby explanation instead of relying on a plot alone.
- Write informative alt text describing relationships or trends, with detailed interpretation in the caption/takeaway. Do not use a filename or repeat the caption verbatim.
- Explain color-coded distinctions with labels or text so color alone is unnecessary. Check contrast and keyboard focus.
- Confirm visible source attribution and the specific reuse license/permission. Inspect exported annotations for private comments, internal results, employer/customer details and personal information.
- Inspect generated image paths in `public/`: keep the largest delivered homepage image at or below 250 KB and publication images at or below 500 KB. Hugo makes WebP widths up to 640/960/1440 and retains the original fallback; check that fallback too. `exact_pixels: true` skips derivatives, so its original PNG is the delivered asset. These byte limits require manual review.
- For a sequence, test Play/Pause with keyboard only, no JavaScript, reduced motion and print. The last frame must explain the method as a static poster. See [the note guide](publishing-a-visual-note.md).
- Check `git status`: no ZIPs, source PDFs, scratch exports or unreviewed figures should be staged. Keep provenance in the manifest and only reviewed web images in page bundles.
