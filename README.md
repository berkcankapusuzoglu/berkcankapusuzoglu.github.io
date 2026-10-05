# Berkcan Kapusuzoglu's portfolio site

This repository builds the public portfolio with Hugo 0.145.0. The production build uses Hugo and does not need Node.js.

## Prerequisites

- Git
- Hugo Extended 0.145.0
- Python 3.13 with Pillow for visual preparation and the full Python test suite; inventory and extraction use only the standard library
- Poppler's `pdftoppm` on `PATH` for PDF preparation
- Node.js 22 or newer and the pinned npm dependencies for the full Python suite's browser fixture and the Pa11y accessibility check

Install the Hugo Extended 0.145.0 release for your operating system from the [Hugo releases page](https://github.com/gohugoio/hugo/releases/tag/v0.145.0). Add the extracted `hugo` executable to `PATH`, then confirm `hugo version` reports `v0.145.0` and `extended`.

## Preview the site

```sh
hugo server
```

Open the local address printed by Hugo. Hugo rebuilds the site as you edit content. A production-style build writes the generated site to `public/`:

```sh
hugo --cleanDestinationDir --minify --panicOnWarning --printPathWarnings
```

## Where content lives

- `data/profile.yaml` holds the public name, role, research themes, professional links, and homepage proof points.
- `content/about/` holds the biography, education, and academic interests.
- `content/publications/` holds one Markdown record per paper. The Publications page shows the complete record on one page.
- `content/writing/` holds Blog posts. The landing page shows each title, opening excerpt, publication date, reading time, and a link to the complete post.
- `content/research/` and `content/leadership/` are retained as unpublished source history. Legacy research URLs redirect to Publications.
- `static/files/resume/Berkcan_Resume.pdf` is the public CV PDF.
- `content/authors/admin/avatar.jpg` is the homepage portrait. Keep the image at this path.

### Add a publication

Create a folder under `content/publications/` with an `index.md` file. Start from the publication archetype or copy this front matter:

```yaml
---
title: "Paper title"
date: 2026-01-15
authors: ["Berkcan Kapusuzoglu", "Coauthor Name"]
venue:
  name: "Proceedings or journal name"
  type: proceedings
status: published
links:
  - label: "Proceedings paper"
    url: "https://example.org/paper"
topics: ["reasoning", "language models"]
featured: false
featured_weight: 10
summary: "A complete, plain-language description of the paper."
contribution: "What the work contributes and Berkcan's role."
---
```

The required fields are `title`, `date`, `authors`, `venue.name`, `venue.type`, `status`, `summary`, and `contribution`. The templates require `topics` and `links` lists even when empty; the release tests expect published papers to have a topic and a canonical paper link. Use a specific link label and a first-party proceedings, publisher, DOI, arXiv, or OpenReview URL. Add a new publication's generated route to `tests/expected-urls.txt`; the tests compare the complete route set. Set `featured: true` to show a paper on the homepage. Smaller `featured_weight` values appear first; use the next available number to choose its position.

### Publish a Blog post

Create `content/writing/<slug>/index.md` with a title, date, description, `summary`, and the post text. Hugo lists these page bundles on the Blog page, newest first. Keep `summary` to one or two opening sentences; it becomes the listing excerpt. Each post should focus on a research question, an engineering lesson, or a useful reading note and link to its supporting publication or source. After publishing, adapt the main point and one takeaway into a LinkedIn post, then link back to the complete article. Do not publish confidential work details or unapproved metrics.

Follow [Publishing a visual Research Note](docs/research/publishing-a-visual-note.md) for the note template, exact-pixel sequence recipe, figure placement and LinkedIn adaptation. Visual notes use the same `visuals` contract as publications.

### Five-minute visual update

For an already reviewed source, follow [Adding a paper visual](docs/research/adding-a-paper-visual.md): inventory the private archive, prepare one named PDF page, add its metadata, preview, validate and commit. Rights review and figure comparison happen before this quick path. The guide includes copyable PowerShell commands and the image/accessibility checklist.

Keep source ZIPs outside Git. Record provenance in [the inventory](docs/research/visual-inventory.yaml); use [the Release 2 backlog](docs/research/visual-release-2.md) to choose the next candidate. Pending figures need specific reuse evidence before preparation. CGD remains the sole homepage visual, and featured order remains CGD, expert pruning, SPEAR-MM.

### Replace the CV

The repository stores the public PDF, not the private resume source that contains a phone number and ZIP code. Do not replace `static/files/resume/Berkcan_Resume.pdf` until the updated source compiles and the resulting PDF has been visually reviewed. Check every page, link, date, and line break. Commit only the approved public PDF; do not add the private resume source.

## Validate changes

Run the same checks used by CI before opening a pull request:

```sh
npm ci
python -m unittest discover -s tests -p "test_*.py" -v
hugo --cleanDestinationDir --minify --panicOnWarning --printPathWarnings
python scripts/site_check.py --public public --expected tests/expected-urls.txt
npm run check:a11y
node --check scripts/check_a11y.mjs
node --check assets/js/research-visuals.js
git diff --check
```

Run `npm ci` before the full Python suite: its sequence-component test launches the Node browser checker, which imports Puppeteer and Pa11y. Pa11y CI checks Home, Publications, a long-author paper, About, Blog, the CGD post, and 404 at desktop and mobile widths. It enforces WCAG 2.0 AA. CI installs the pinned Node tools before tests; Node is not part of the Hugo production build. Use the Python interpreter with Pillow described in the visual guide; a standard-library-only interpreter cannot run all asset tests.

## Review and deployment

Create a feature branch, commit the change, and push it for review. Open a pull request against `master` and wait for the Hugo, route, Python, and Pa11y checks to pass. Review the generated site artifact and the page changes before merging. A push to `master` deploys the built site to the GitHub Pages branch. After the workflow succeeds, open the live site and confirm the updated pages and CV load correctly.

To roll back a bad release, create a reviewed revert commit for the merge or offending commit and merge it to `master`. The deployment workflow then publishes the reverted site. Keep the pull request and its checks as the audit trail.
