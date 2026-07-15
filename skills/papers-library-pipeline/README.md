# papers-library-pipeline

[中文说明](README.zh-CN.md)

**Agent Skill (stage A):** harvest, score, download, and catalog academic papers into a local library with an Excel triage list. No PDF→Markdown, no OCR, no static site.

Part of the `papers-to-knowledge-base` family. For intake/routing use the orchestrator; for Markdown/site use `papers-knowledge-site`.

Compatible with **Cursor**, **Claude Code**, **Codex**, **OpenCode**, **Pi**, and hosts that follow the [Agent Skills](https://agentskills.io) `SKILL.md` layout.

## What you get

| Piece | Role |
|-------|------|
| `SKILL.md` | Agent rules for library-only work |
| `scripts/papers_library_pipeline/` | OpenAlex/Crossref harvest, PDF fetch (httpx), PDF-only manifest sync, Excel export |
| `references/checklist.md` | Library acceptance checks |

**Acceptance flags:** write `accepted` (preferred) or `selected` (alias). `--selected-only` treats either as true.  
**PDF filenames:** `{local_id}.{sanitized_title}.pdf` only (e.g. `1001.Guinier_approximation.pdf`).  
**A-only dirs:** creates `*-pdf/`, `*-candidates/`, `*-catalog/` — not `*-md/` / `*-web/`.  
**Source health:** `{DOMAIN}-catalog/source-health.json` stores OpenAlex UTC-day skip and last-good Sci-Hub mirror.  
**Triage gate:** ask Full AI / Script-only / Hybrid before review writes (see `SKILL.md`).  
**Unit tests** live outside this skill: [`../../_dev/papers-library-pipeline/`](../../_dev/papers-library-pipeline/).  
**Parallel subagents** (when the host supports them): [references/parallel-subagents.md](references/parallel-subagents.md).

## Install

Link into **the skills directory of the agent you use** (Cursor / Claude Code / Codex / …).  
See the [repo README](../../README.md) — do not install into every host at once.  
Prefer also linking the orchestrator so intake + routing stay available.

## Scripts setup

Shared uv workspace at the **repo root** (with stage B):

```bash
# from repo root
uv sync
# copy scripts/domain_config.example.json → {ROOT}/domain_config.json
export DOMAIN_KB_CONFIG=/path/to/domain_config.json
uv run python -m papers_library_pipeline.run_harvest
uv run python -m papers_library_pipeline.pdf_fetch fetch-batch {ROOT}/FIELD-candidates/candidates.json \
  --pdf-dir {ROOT}/FIELD-pdf --manual {ROOT}/FIELD-catalog/manual-needed.md \
  --selected-only --assign-ids
uv run python -m papers_library_pipeline.sync_manifest
uv run python -m papers_library_pipeline.export_excel
```

Excel output: **`{DOMAIN}-catalog/literature.xlsx`**.

Tell the agent: *“Use papers-library-pipeline to harvest and download papers for …”*

## Layout

```text
papers-library-pipeline/
  SKILL.md
  README.md / README.zh-CN.md
  references/checklist.md
  scripts/
    pyproject.toml
    domain_config.example.json
    seed_works.example.json
    papers_library_pipeline/
```

## Boundaries

- **In scope:** harvest, triage, PDF download, catalog, Excel
- **Out of scope:** MarkItDown, PaddleOCR, `{DOMAIN}-md/`, `{DOMAIN}-web/`
