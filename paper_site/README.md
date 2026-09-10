# AHN paper draft — internal team-review page

A static, single-file web page that presents the **current** manuscript draft so
teammates can read and review it in a browser.

- **Not** the NAACL/ARR submission, an anonymized artifact, a preprint, or a
  replacement for `manuscript/*.md`.
- Presentation layer only: it renders the manuscript source, the verified
  bibliography (`manuscript/REFERENCES_VERIFIED.bib`), and the frozen publication
  exhibits (`outputs/publication_exhibits/`). It does not modify or reinterpret
  any scientific content.
- The page carries `<meta name="robots" content="noindex, nofollow, noarchive">`
  and a `robots.txt` that disallows all crawlers.

## Files

```
paper_site/
  build.py        regenerates index.html from the manuscript + bib + exhibits
  index.html      the generated page (committed, so no build step is needed to read it)
  style.css       styling (restrained academic layout, print-friendly)
  app.js          ~30 lines: table-of-contents active-section highlight
  figures/        copies of the 4 main figures (PNG + SVG) from outputs/publication_exhibits/main/
  robots.txt      disallow: /
  .nojekyll       marker (only relevant if ever served from GitHub Pages)
  README.md       this file
```

## Local preview

From the repo root (or from `paper_site/`):

```bash
python3 -m http.server 8731 --directory paper_site
```

then open <http://localhost:8731/> . Any static file server works; opening
`paper_site/index.html` directly with `file://` also works (the figures and
`style.css` load with relative paths).

## Rebuilding after the manuscript changes

```bash
python3 paper_site/build.py      # run from the repo root
```

This re-reads `manuscript/ABSTRACT.md … CONCLUSION.md`,
`manuscript/REFERENCES_VERIFIED.bib`, and `outputs/publication_exhibits/main/`,
and rewrites `paper_site/index.html`. It stamps the page with the current git
commit and today's date. Only Python 3.8+ standard library is used.

If you add or replace a figure in `outputs/publication_exhibits/main/`, copy the
new PNG/SVG into `paper_site/figures/` before rebuilding.

## Current deployment

A **private, access-controlled** copy is deployed as a Claude Artifact:

```
https://claude.ai/code/artifact/1d2c3864-feb1-4334-b1a8-dc59406fade7
```

- **Private by default** — only the artifact owner's Claude account can open it
  until the owner shares it from the page's *Share* menu.
- Not publicly searchable or indexed; served behind claude.ai authentication.
- It is a single self-contained HTML file (assets inlined) generated with
  `python3 paper_site/build.py --artifact <out.html>`. Rendered content is
  identical to `index.html`; only the packaging differs (external CSS/JS/figures
  are inlined, and dead figure-download links are inert in the sandbox).
- To refresh it after the manuscript changes: rebuild with `--artifact` and
  re-publish the same file path from the Claude Code session that created it
  (this keeps the URL).

See `manuscript/TEAM_PAPER_PAGE_AUDIT.md` for the full deployment + anonymity
assessment.

## Other sharing options

**Do not deploy publicly** while an anonymous NAACL/ARR submission is in
preparation. Private alternatives:

| option | private? | effort | notes |
|---|---|---|---|
| `python3 -m http.server` on a teammate call / screen-share | yes | none | simplest; nothing leaves the machine |
| zip `paper_site/` and share the folder | yes | none | teammates open `index.html` locally |
| private Claude Artifact (default-private, link shared to named teammates) | yes | low | one URL, access-controlled, not indexed |
| Netlify / Vercel / Cloudflare Pages **with password / access control** | yes* | medium | acceptable if the deploy is genuinely access-gated |
| GitHub Pages | **NO — Pages is always public even from a private repo** | low | do **not** use while the submission is anonymous |

The page is deliberately buildable and viewable without any hosting.
