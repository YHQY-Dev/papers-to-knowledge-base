# Site acceptance checklist

Fill `{DOMAIN}`, `{LANG}`. Assumes PDFs + acceptance list already exist (from `papers-library-pipeline` or user-provided).

## Prerequisites

- [ ] Accepted PDFs under `{DOMAIN}-pdf/` (verify `%PDF` magic)
- [ ] Acceptance list present (`literature.xlsx` and/or `manifest.json` / candidates with `accepted` or alias `selected`)
- [ ] `{LANG}` and OCR preference known from intake (or asked if invoked alone)
- [ ] No bulk paper discovery attempted in this skill

## Convert (PDF → MD)

- [ ] Convert waterfall: PaddleOCR MCP if ready and needed, else MarkItDown
- [ ] Missing / empty OCR token does **not** block the pipeline
- [ ] No AI Studio token committed to git
- [ ] Each accepted id has `{DOMAIN}-md/{id}/content.md` (+ `convert_meta.json`, `imgs/` as needed)
- [ ] Optional: `citation_extract` for DOI/ref clues from MD (does not download new PDFs)

## Site (`{DOMAIN}-web/`)

- [ ] `index.html` opens without npm (`file://` or any static host)
- [ ] Chapters + glossary with bidirectional term links; glossary ids locked before parallel chapter work
- [ ] Math OK (KaTeX); plain `Å`; no raw `\unicode{...}` visible
- [ ] Citations = DOI / OA URLs only
- [ ] Public site does **not** link into local `*-pdf/` or `*-md/` trees
- [ ] Humans read PDFs; MD is for AI authoring of the site

## Process

- [ ] Intake / handoff confirmed before mass convert or site rewrite
- [ ] Missing PDFs sent back to `papers-library-pipeline` or listed in `manual-needed`
