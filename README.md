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
| Scripts that generate figures | `scripts/` (`rayleigh_figure.py`, `foregrounds_figure.py` → `static/images/`) |
| Train travel stats (Misc → Trains) | `data/trains.json` and `assets/images/trains_map_tracks.svg`, written by the rail_travels export (see below) |
| Name, email, menu | `hugo.toml` |

To add a research project, copy `content/research/rayleigh.md`, edit it, and drop the image in `static/images/`.

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

## Self-hosting on a solar-powered Raspberry Pi

A step-by-step plan (Freebox setup, security, solar sizing for Paris, parts and wiring) is in [`docs/self-hosting-solar.md`](docs/self-hosting-solar.md). It is not published on the site.

## Updating the train statistics

Trips are logged in a separate private project, `~/Documents/Misc/rail_travels` (local page: `python3 rt.py serve`). Its export writes only aggregates into this repo, `data/trains.json` (months, never exact dates or times) and the map `assets/images/trains_map_tracks.svg`:

```bash
cd ~/Documents/Misc/rail_travels && python3 rt.py export
```

Then check with `hugo server` and commit those two files here.
