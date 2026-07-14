# Acceptance checklist (library / stage A)

Fill `{DOMAIN}`, `{N}`.

## Library

- [ ] `run_harvest` + `pdf_fetch` + `sync_manifest` + `export_excel` used
- [ ] `domain_config.json` set; optional `seed_works.json`
- [ ] Candidates deduped; triage with `accepted` (or alias `selected`) + `local_id`
- [ ] ≥ `{N}` items named `{id}.{title}.pdf` under `{DOMAIN}-pdf/`
- [ ] PDFs verify as `%PDF` (magic header)
- [ ] `{DOMAIN}-catalog/literature.xlsx` exists with required columns:
  `local_id`, `title`, `type`, `doi`, `isbn`, `year`, `script_score`, `ai_score`,
  `accepted`, `decision`, `reason`, `pdf_status`, `pdf_path`, `notes`
- [ ] `pdf_status` / `pdf_path` filled from disk after download (`export_excel`)
- [ ] Rejected / backfill rows remain in Excel with reasons
- [ ] `manual-needed.md` lists failures; `manifest.json` matches PDF disk
  (no need to create md/web for A-only)

## Out of scope for A-only

- [ ] No `{DOMAIN}-md/` or `{DOMAIN}-web/` created by A scripts
- [ ] No PDF→Markdown / MarkItDown / PaddleOCR OCR steps in this stage

## Process

- [ ] Intake vars (`{DOMAIN}`, `{ROOT}`, `{N}`, `{THEMES}`) confirmed before bulk work
- [ ] Vars documented in `{ROOT}/specs/` when using the orchestrator
- [ ] If host supports subagents and work is large: parallel harvest/review shards used; parent merged before download ([parallel-subagents.md](parallel-subagents.md))
