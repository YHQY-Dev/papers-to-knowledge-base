---
name: papers-library-pipeline
description: >-
  Use when the user wants to harvest, score, download, or catalog academic
  papers into a local literature library with an Excel triage list (文献库,
  打分下载, Excel list, OpenAlex/Crossref harvest)—not for PDF→Markdown,
  OCR, static knowledge sites, or general web scraping.
license: MIT
compatibility: Agent Skills hosts (Cursor, Claude Code, Codex, OpenCode, Pi)
---

# Papers library pipeline (stage A)

Harvest → triage → PDF download → catalog → **Excel export**.  
Humans read PDFs; this skill does **not** convert to Markdown or build a site.

Sibling: orchestrator `papers-to-knowledge-base`; site stage is `papers-knowledge-site`.

Human docs: [README.md](README.md) · [README.zh-CN.md](README.zh-CN.md) · [references/checklist.md](references/checklist.md).

## When NOT to use

- PDF→Markdown, PaddleOCR / MarkItDown, or static HTML site work → use `papers-knowledge-site`
- Full intake + routing (library vs site vs both) → use `papers-to-knowledge-base` first
- Unrelated scraping or CMS work

## Hard rules

1. **No PDF→MD**, **no static site**, **no OCR MCP** in this skill.
2. Parameterize `{DOMAIN}` / `{ROOT}`; never hard-code project-only paths.
3. Reuse `scripts/papers_library_pipeline/` (HTTP = **httpx**).
4. Assign `local_id` before batch download (`fetch-batch --assign-ids`). Sync manifest after assets change.
5. Excel lives at `{DOMAIN}-catalog/literature.xlsx` (required handoff artifact).

## Intake assumption

When invoked from `papers-to-knowledge-base`, assume **Q0 + Phase 1–2** intake is done and confirmed.

**If invoked alone:** require `{DOMAIN}`, `{ROOT}`, `{N}`, `{THEMES}` (and optional scope/seeds). If any are missing, ask or refuse—do not start harvest/download.

| Var | Meaning | Example |
|-----|---------|---------|
| `{DOMAIN}` | slug | `battery` |
| `{ROOT}` | asset root | `D:/work/battery-kb` |
| `{N}` | target accepted PDF count | `100` |
| `{THEMES}` | search themes | list |

## Pipeline

```text
1 Harvest → 2 Script + AI triage → 3 pdf_fetch --assign-ids
→ 4 sync_manifest → 5 export_excel → Checklist
```

| Stage | Do |
|-------|----|
| 1 | `run_harvest`; prefer reviews/books; optional `seed_works.json` |
| 2 | AI vs scope; set `accepted` (or alias `selected`) + scores/reasons |
| 3 | `fetch-batch --selected-only --assign-ids` (honors `accepted` **or** `selected`); require `%PDF` |
| 4 | `sync_manifest` (PDF-only by default; `--include-md` if MD already exists); `manual-needed.md` |
| 5 | `export_excel` → `{DOMAIN}-catalog/literature.xlsx` |
| 6 | [checklist.md](references/checklist.md) |

Rejected / backfill rows stay in Excel with reasons.

## Excel columns

| Column | Meaning |
|--------|---------|
| local_id | Local id |
| title | Title |
| type | article / review / book / chapter… |
| doi | DOI (optional) |
| isbn | ISBN (optional) |
| year | Year |
| script_score | Coarse script score |
| ai_score | AI score (optional) |
| accepted | yes/no (download / handoff). Alias field in JSON: `selected` |
| decision | download / backfill / reject… |
| reason | Why accepted or rejected |
| pdf_status | downloaded / failed / not_attempted |
| pdf_path | Path if present |
| notes | Free notes |

## Directory contract

```text
{ROOT}/
  domain_config.json
  {DOMAIN}-candidates/candidates.json
  {DOMAIN}-pdf/{local_id}.{title}.pdf   # e.g. 1001. Guinier_approximation.pdf
  {DOMAIN}-catalog/
    manifest.json
    ai-reviews/
    manual-needed.md
    literature.xlsx
```

No `{DOMAIN}-md/` or `{DOMAIN}-web/` required for A-only.

## Bundled code

Copy `scripts/` into `{ROOT}` or set `PYTHONPATH` to skill `scripts/`.  
`domain_config.example.json` → `{ROOT}/domain_config.json`.  
Optional seeds: `seed_works.example.json` → `{DOMAIN}-candidates/seed_works.json`.

| Module | Use |
|--------|-----|
| `run_harvest` | OpenAlex+Crossref → candidates |
| `pdf_fetch` | search/download PDF (`--assign-ids`) |
| `sync_manifest` | Rebuild catalog from PDF disk (`--include-md` optional) |
| `export_excel` | Write `literature.xlsx` |

```bash
pip install -r scripts/requirements.txt
export DOMAIN_KB_CONFIG=/path/to/domain_config.json
cd scripts
python -m papers_library_pipeline.run_harvest
python -m papers_library_pipeline.pdf_fetch fetch-batch ../{DOMAIN}-candidates/candidates.json \
  --pdf-dir ../{DOMAIN}-pdf --manual ../{DOMAIN}-catalog/manual-needed.md \
  --selected-only --assign-ids
python -m papers_library_pipeline.sync_manifest
python -m papers_library_pipeline.export_excel
```

`pdf_fetch` order: OA → mirrors → manual.  
`ai_*_threshold` in config are **AI triage hints**, not enforced by scripts.

## Anti-patterns

- Converting PDFs to Markdown or calling OCR from this skill
- Building `{DOMAIN}-web/` here
- Downloading without `local_id`
- Skipping Excel export before handoff to B
- Rewriting OpenAlex/Crossref/`pdf_fetch` clients without need
