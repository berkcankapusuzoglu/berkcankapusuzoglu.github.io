# How to edit the site

Most changes only require editing a Markdown or YAML file. Hugo rebuilds the preview when you save.

## Preview your changes

Open a terminal in this repository and run:

```powershell
hugo server
```

Open <http://localhost:1313/>. Press `Ctrl+C` in the terminal to stop the server.

## Find the text you want to change

| What you want to edit | File or folder |
| --- | --- |
| Homepage name, headline, bio, links, and research themes | `data/profile.yaml` |
| Homepage news and career updates | `data/updates.yaml` |
| Homepage browser title and description | `content/_index.md` |
| Homepage section headings, supporting sentences, and button text | `layouts/index.html` |
| About page | `content/about/_index.md` |
| Navigation labels and order | `config/_default/menus.yaml` |
| Publications | `content/publications/` |
| Blog introduction | `content/writing/_index.md` |
| Blog posts | `content/writing/` |

Edit Markdown below the second `---` line. Edit page settings between the two `---` lines. Keep YAML indentation consistent and use spaces, not tabs.

To reorder navigation links, change their `weight` values in `config/_default/menus.yaml`. Lower numbers appear first. Removing a navigation link does not delete its page.

## Add a Blog post

Create a draft from the Blog template:

```powershell
hugo new content writing/my-post/index.md
```

Replace `my-post` with a short lowercase name separated by hyphens. Open the generated `content/writing/my-post/index.md` and update:

- `title`: the headline shown on the post and Blog page
- `date`: the publication date in `YYYY-MM-DD` format
- `description`: the browser and search description
- `summary`: one or two sentences shown on the Blog page
- The Markdown below the second `---`: the full article

Preview drafts with:

```powershell
hugo server -D
```

When the post is ready, change `draft: true` to `draft: false`. The normal `hugo server` preview will then include it.

To add an image, put it in the post folder, for example `content/writing/my-post/diagram.png`, and use:

```markdown
![Plain-language description of the image](diagram.png)
```

For a figure with a caption and source link, use:

```markdown
{{< archive-figure src="diagram.png" alt="Describe what the figure shows" caption="A concise caption." source_url="https://example.com/original" >}}
```

## Add a homepage update

Open `data/updates.yaml`, copy the first four-line entry, and edit its values. Keep the newest item first:

```yaml
- date: "Sep. 2026"
  date_iso: "2026-09"
  text: "A short, factual update."
  url: "/publications/example.html"
```

Use `YYYY-MM` for `date_iso`. The `url` can point to a page on this site or an external article.

## Add a publication

Create a folder under `content/publications/`, copy `archetypes/publications.md` to its `index.md`, and fill in every field. Use an existing publication with a similar status as a reference. Set `featured: true` only when the paper should also appear on the homepage.

## Add or remove a section

A top-level section normally has:

1. A folder such as `content/writing/` containing `_index.md`.
2. A matching layout under `layouts/` when it needs a custom design.
3. An entry in `config/_default/menus.yaml` when it should appear in navigation.

Copy a similar existing section before changing templates. Deleting a menu entry only hides the link. Delete content only when you intend to remove the page itself.

## Check before publishing

Run:

```powershell
hugo --cleanDestinationDir --minify --panicOnWarning --printPathWarnings
python -m unittest discover -s tests -p "test_*.py" -v
git diff --check
```

If you add or remove a page, update `tests/expected-urls.txt` with its generated route. Commit the source files, not the generated `public/` folder.
