# Benjamin Beringue — personal website

Static site built with [Hugo](https://gohugo.io). Content is plain Markdown.

## Editing content

| What | Where |
|---|---|
| Landing page "about" text and photo | `content/_index.md` |
| Research projects (one file each) | `content/research/*.md` — front matter: `title`, `link`, `image`, `weight` (order) |
| Publications list | `data/publications.yaml` |
| Publications intro text | `content/publications/_index.md` |
| CV page | `content/academic_cv.md` |
| Images, PDFs, CSS, JS | `static/` (served as-is) |
| Name, email, menu | `hugo.toml` |

To add a research project, copy `content/research/sps4lat.md`, edit it, and drop the image in `static/images/`.

## Preview locally

```bash
hugo server
```

Then open http://localhost:1313.

## Build

```bash
hugo --minify
```

The finished site is written to `public/`. You can copy that folder to any web server (e.g. a Raspberry Pi) with `rsync`.
Pushing to `master` deploys to GitHub Pages through `.github/workflows/hugo.yml`.

Theme adapted from templates by [Mauricio Urraco](https://github.com/murraco) and [Nathan Randecker](https://github.com/nrandecker).
