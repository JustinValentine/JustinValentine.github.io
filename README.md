# Personal Site

A small static personal site: a homepage, a projects page, notes (posts), categories, an about page, and RSS. Plain HTML and one stylesheet, no build step.

## Edit

Pages are generated from `src/` by `build.py` (Python 3, standard library only). Edit the files in `src/`, then run:

    python3 build.py

- **Posts:** each project or note is `src/posts/<slug>.html`: a few `key: value` lines (title, date, topics, summary, image, series, math), a `---` line, then the body as HTML. The docstring at the top of `build.py` lists the keys. Dates can be a day, a month or a year (`2023-12-08`, `2026-10`, `2024`). Images go in `images/`.
- **Topics:** the list is `TOPICS` in `build.py`. Each topic gets a page at `topics/<slug>/`.
- **Series:** posts with the same `series:` key list each other in date order (for now, `haptic-wrist`).
- **Generated:** `index.html`, `posts/*/index.html`, `topics/`, `about/index.html` (from `src/about.html`), `wrist/index.html` (from `src/wrist.html`), `index.xml`, and redirects at `projects/` and `categories/`. Don't edit these by hand; they're overwritten.
- **Wrist page:** `src/wrist.html` is the overview of the Alberta wrist at `/wrist/`, the short address printed on the CVRG lab brochure. Its styles are at the end of `css/style.css`.
- **CV:** put your current CV at `cv.pdf` in the site root. Every page links to it.
- **Photos from a phone:** strip the location data before publishing. iPhone photos and videos carry GPS coordinates.

## Preview

Run `python3 build.py`, then open `index.html` in a browser. The links are relative, so no local server is needed.
