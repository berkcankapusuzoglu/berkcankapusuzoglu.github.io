# Berkcan Kapusuzoglu's portfolio site

This repository builds the public portfolio with Hugo 0.145.0. The production build uses Hugo and does not need Node.js.

## Prerequisites

- Git
- Hugo Extended 0.145.0
- Node.js 22 or newer only when running the Pa11y accessibility check

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
- `content/research/` holds the research overview and three research-area pages.
- `content/leadership/` and `content/about/` hold the leadership and biography pages.
- `content/publications/` holds one Markdown record per paper.
- `content/writing/` holds Research Notes. The landing page is intentionally an honest empty state until a note is ready.
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

The required fields are `title`, `date`, `authors`, `venue.name`, `venue.type`, `status`, `summary`, and `contribution`. Links and topics are optional. Use a specific link label and a first-party proceedings, publisher, DOI, arXiv, or OpenReview URL. Set `featured: true` to show a paper on the homepage. Smaller `featured_weight` values appear first; use the next available number to choose its position.

### Publish a Research Note

Create `content/writing/<short-name>.md` with a title, date, description, and the note text. Keep it focused on a research question, an engineering lesson, or a useful reading note. Link to the supporting publication or source. After publishing, adapt the note's main point and one takeaway into a LinkedIn post, then link back to the full note. Do not publish confidential work details or unapproved metrics.

### Replace the CV

The repository stores the public PDF, not the private resume source that contains a phone number and ZIP code. Do not replace `static/files/resume/Berkcan_Resume.pdf` until the updated source compiles and the resulting PDF has been visually reviewed. Check every page, link, date, and line break. Commit only the approved public PDF; do not add the private resume source.

## Validate changes

Run the same checks used by CI before opening a pull request:

```sh
python -m unittest discover -s tests -p "test_*.py" -v
hugo --cleanDestinationDir --minify --panicOnWarning --printPathWarnings
python scripts/site_check.py --public public --expected tests/expected-urls.txt
npm ci
npm run check:a11y
node --check scripts/check_a11y.mjs
git diff --check
```

Pa11y CI checks the home, research, publications, a long-author paper, leadership, About, Research Notes, and 404 pages at desktop and mobile widths. It enforces WCAG 2.0 AA. CI installs the pinned Node tools; Node is not part of the Hugo production build.

## Review and deployment

Create a feature branch, commit the change, and push it for review. Open a pull request against `master` and wait for the Hugo, route, Python, and Pa11y checks to pass. Review the generated site artifact and the page changes before merging. A push to `master` deploys the built site to the GitHub Pages branch. After the workflow succeeds, open the live site and confirm the updated pages and CV load correctly.

To roll back a bad release, create a reviewed revert commit for the merge or offending commit and merge it to `master`. The deployment workflow then publishes the reverted site. Keep the pull request and its checks as the audit trail.
