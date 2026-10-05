# Publishing a visual Research Note

Write a note around one reader question, one diagram and a supported practical lesson. Use [the published CGD note](../../content/writing/critique-guided-distillation-refinement/index.md) as a working example and complete [the figure rights and quality checklist](adding-a-paper-visual.md) before copying an image into a note.

## Structure and front matter

Create `content/writing/<slug>/index.md`. Use a lowercase hyphenated slug and a deliberate public date. A draft can use `draft: true` and `hugo server -D`; remove the draft flag for publication.

```yaml
---
title: "A specific research question"
date: 2026-10-05
description: "The question, method and scope in one sentence."
summary: "A short index description of the lesson."
linkedin:
  thesis: "One supported idea to lead the adaptation."
  takeaways:
    - "A practical implication."
    - "A limitation worth remembering."
  sharing: "Link to this canonical note; adapt rather than reproduce it."
visuals:
  - id: method-sequence
    file: media/method-overview.png
    role: lead
    exact_pixels: true
    alt: "Describe the complete diagram's stages and relationships."
    caption: "Explain the diagram and the setting it represents."
    takeaway: "One supported practical lesson."
    source_label: "Author et al. (year), Figure 1"
    source_url: "https://example.org/canonical-paper"
    license: "Specific verified reuse license or permission"
    sequence:
      - file: media/method-overview.png
        label: "Starting point"
        duration: 3000
        focus: {x: 0, "y": 0, width: 50, height: 50}
      - file: media/method-overview.png
        label: "Complete method"
        duration: 3000
        callout: "Explain the complete method in visible prose."
---
```

Replace placeholders with verified prose and sources. Note visuals have the same required fields and local-resource rules as publication visuals. `sequence` is optional for a static figure. Use `lead`, `result` or `supporting`, and unique visual IDs. `linkedin` fields are editorial metadata, not rendered keywords. Writing is listed newest first; no publication-specific authors/venue fields are required for a note.

Write the body in this order:

1. Reader question: what decision or failure makes the method useful?
2. Diagram: introduce the method and place `{{< research-visual >}}` on its own line.
3. Interpretation: explain the stages and distinguish training from deployment where relevant.
4. Result: name the evaluated setting and comparison; add a result visual only if it helps.
5. Limits: explain what the result does not establish and what needs further evaluation.
6. Takeaway: give a practical action a reader can test.
7. Citation: link the canonical paper and the site's supporting publication, with authors/title/venue/year.

Place one shortcode per visual, in `visuals` order. A mismatched count fails the build. If you use no shortcodes, all figures follow the prose. Keep the full diagram available; never turn an unpictured deployment claim into a fabricated panel. Explain such a claim in prose with a section citation.

## Prepare an exact-pixel sequence

Use the Pillow interpreter from [the visual guide](adding-a-paper-visual.md#before-preparing-a-figure). The source must be an approved PNG. Save a recipe as `content/writing/<slug>/sequence-recipe.yaml`, using **JSON syntax** (the YAML 1.2 subset accepted by this CLI):

```json
{
  "file": "method-overview.png",
  "sequence": [
    {"label": "Starting point", "duration": 3000, "focus": {"x": 0, "y": 0, "width": 50, "height": 50}},
    {"label": "Complete method", "duration": 3000, "callout": "Explain the complete method."}
  ]
}
```

Choose meaningful regions for your diagram; the example coordinates are placeholders. Run from the repository root, changing the note slug:

```powershell
& $assetPython scripts/research_assets.py sequence --source 'content/publications/2026-critique-guided-distillation/media/cgd-overview.png' --recipe 'content/writing/<slug>/sequence-recipe.yaml' --output-dir 'content/writing/<slug>/media'
```

The output directory must be exactly `content/writing/<note>/media/`. The recipe `file` is a simple `.png` filename without directories. The command copies that one PNG byte for byte, emits checksum/dimension metadata and ordered repeated `media/<file>` references, and refuses an existing destination. Use a new filename for revisions. Copy its emitted `file` and `sequence` into front matter; supply the remaining visual fields yourself. Retain the recipe and provenance record.

Each recipe step needs a nonempty `label` and positive integer `duration` in milliseconds. `focus` uses numeric percentages (`x`, `y`, `width`, `height`) of the whole image; width/height must be positive and the region must stay within 0–100. It draws a CSS outline without cropping or painting pixels. Optional `callout` adds visible prose. Front matter can omit duration (1800 ms default), but the recipe requires it. Set `exact_pixels: true` to serve the unchanged PNG; inspect its byte size because this skips WebP derivatives.

The last step is the initial poster with no JavaScript, reduced motion and print. With reduced motion enabled, the button becomes `Next step` for manual advancement. Callouts and step labels remain readable independently of animation. Playback starts only when requested, pauses when the tab is hidden and stops at the final frame. Test the sequence with keyboard focus, Play/Pause, reduced motion enabled, JavaScript disabled and print preview.

## Preview, validate and share

Run `hugo server` (or `hugo server -D` for a draft), open Research Notes and follow the new note. Inspect 360×800 and 1440×900, including sideways scrolling of a dense diagram. When publishing a new note, add `/writing/<slug>.html` to `tests/expected-urls.txt`; the unit tests compare the complete generated route set. Stop the server, then run [the full validation commands](../../README.md#validate-changes) with the Pillow interpreter. Check image budgets, source attribution and confidential annotations with [the shared checklist](adding-a-paper-visual.md#quality-accessibility-and-confidentiality-checklist).

Commit the note's `index.md`, reviewed `media/` image(s), recipe, updated provenance and `tests/expected-urls.txt` explicitly. Preview before pushing this release, then use [the PR, deployment and revert workflow](../../README.md#review-and-deployment). Confirm the canonical note and index after deployment.

For LinkedIn:

- Start with `linkedin.thesis` and one reader question, then select two or three supported takeaways.
- Name the evaluated setting and retain a material limitation. Verify every metric and venue/status claim against its evidence.
- Link to the deployed canonical note; copy its actual URL, including the site's `.html` suffix. Keep the full argument and citation on the site.
- If sharing an image, confirm permission covers that platform, keep attribution/labels readable and supply alt text. Do not add private annotations or internal results.
- Review the adaptation as its own public text. Edit the canonical note when the underlying explanation changes; writing sharing metadata does not publish a social post.
