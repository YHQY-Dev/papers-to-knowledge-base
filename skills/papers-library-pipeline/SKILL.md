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

Human docs: [README.md](README.md) · [README.zh-CN.md](README.zh-CN.md) · [references/checklist.md](references/checklist.md) · [references/parallel-subagents.md](references/parallel-subagents.md).

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
| `{ROOT}` | asset root | **default: current directory** (`"."`) |
| `{N}` | target accepted PDF count | `100` |
| `{THEMES}` | search themes | list |

## Pipeline

```text
1 Harvest → 2 Triage (ask mode first) → 3 pdf_fetch --assign-ids
→ 4 sync_manifest → 5 export_excel → Checklist
```

| Stage | Do |
|-------|----|
| 1a | **Per theme (separate shell calls):** `run_harvest --theme "…"`. Writes shards only. Budget **≥ 2 min per theme** call. Within theme: OpenAlex ∥ Crossref → separate shard files |
| 1b | After all themes: `run_harvest --integrate` → dedupe-merge shards into `candidates.json` |
| 1c | **Refs (separate from harvest):** `expand_refs --next` or `--doi …` — **one paper per call**. Do not expand refs inside `run_harvest` |
| 2 | **Hard gate — ask the user before any triage writes** (see below) |
| 3 | `fetch-batch --selected-only --assign-ids` (honors `accepted` **or** `selected`); require `%PDF`. Sci-Hub: probe once, prefer last-known-good (also in `source-health.json`) |
| 4 | `sync_manifest` (PDF-only by default; `--include-md` if MD already exists); `manual-needed.md` |
| 5 | `export_excel` → `{DOMAIN}-catalog/literature.xlsx` |
| 6 | [checklist.md](references/checklist.md) |

### Harvest & refs — agent invocation (mandatory)

**Never** run all themes + reference expand in one long process (it will be killed by timeouts). Your screenshot’s `harvest theme` then `refs from '10.3390/…'` in the same run is the wrong pattern.

```text
# optional once
uv run python -m papers_library_pipeline.run_harvest --seeds-only

# ONE theme per invocation (timeout ≥ 2 minutes each)
uv run python -m papers_library_pipeline.run_harvest --theme "Ag2Se Seebeck coefficient"
uv run python -m papers_library_pipeline.run_harvest --theme "beta-Ag2Se thermal properties"
# … repeat for every search_themes entry …

# after all themes
uv run python -m papers_library_pipeline.run_harvest --integrate

# ONE paper's refs per invocation (timeout ≥ 2 minutes each); repeat --next
uv run python -m papers_library_pipeline.expand_refs --next
uv run python -m papers_library_pipeline.expand_refs --doi 10.1016/j.mattod.2013.05.004
```

- Theme harvest and `expand_refs` are **different stages** — do not chain them in one command.
- Prefer many short agent/shell turns over one mega-run.
- OpenAlex UTC-day skip still applies (`source-health.json`).

Rejected / backfill rows stay in Excel with reasons.

### Stage 2 triage gate (required)

**Do not** start writing `accepted` / `ai_score` / `reason` until the user chooses a mode. Present these options and the cost trade-offs:

| Mode | Behavior | Tell the user |
|------|----------|---------------|
| **Full AI** | Read title/abstract (optional short notes) per paper; set `ai_score`, `accepted`, `reason` | **Slower** and **token-heavy**. Prefer **3–8 parallel subagents** on disjoint candidate slices when the host supports it (see [parallel-subagents.md](references/parallel-subagents.md)) |
| **Script-only** | Use `script_score` + config thresholds (`ai_download_threshold` / `ai_backfill_threshold` as hints) → `accepted` / backfill / reject | Fast, **no LLM tokens**; may miss or over-accept |
| **Hybrid** | Script coarse filter; AI only for scores in the mid band (between backfill and download thresholds) | Medium cost; good default for large candidate sets |

Recommendation to user: hybrid for large sets; script-only for dry runs; full AI when quality outweighs cost/latency.

After the user answers, run that mode only. If they pick Full AI or Hybrid and subagents are available, offer parallel shards.

## Parallel subagents (when available)

If the host can dispatch **subagents**, use **multiple in parallel** for independent stage-A work — especially harvest shards and review/scoring batches. Details: [references/parallel-subagents.md](references/parallel-subagents.md).

**Before AI review:** complete the Stage 2 triage gate (ask Full AI / Script-only / Hybrid). For Full AI / Hybrid, warn about latency and token cost, then prefer parallel shards.

**Do parallelize:** theme/query shards; disjoint candidate slices for AI triage (`ai_score`, `accepted`, `reason`).  
**Do not parallelize without a single merger:** writing `candidates.json`, assigning `local_id`, `fetch-batch`, final `export_excel`.

Pattern: parent splits → N subagents return structured JSON → parent dedupes/merges → one download + Excel pass.  
If subagents are unavailable, run the pipeline sequentially (same stages).

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
  {DOMAIN}-candidates/
    candidates.json
    shards/                 # harvest theme×api temps; merged when harvest finishes
    seed_works.json         # optional
  {DOMAIN}-pdf/{local_id}.{title}.pdf   # e.g. 1001. Guinier_approximation.pdf
  {DOMAIN}-catalog/
    manifest.json
    source-health.json   # OpenAlex UTC-day skip + Sci-Hub preferred mirror
    ai-reviews/
    manual-needed.md
    literature.xlsx
```

No `{DOMAIN}-md/` or `{DOMAIN}-web/` required for A-only.

## Bundled code

From the **repo root** (shared uv workspace with stage B):

```bash
uv sync
# Tokens: copy repo-root .env.example → .env and set OPENALEX_API_KEY=
# https://openalex.org/settings/api
export DOMAIN_KB_CONFIG=/path/to/domain_config.json
# one theme at a time, then integrate; refs separately
uv run python -m papers_library_pipeline.run_harvest --theme "myfield review"
uv run python -m papers_library_pipeline.run_harvest --integrate
uv run python -m papers_library_pipeline.expand_refs --next
uv run python -m papers_library_pipeline.pdf_fetch fetch-batch {ROOT}/{DOMAIN}-candidates/candidates.json \
  --pdf-dir {ROOT}/{DOMAIN}-pdf --manual {ROOT}/{DOMAIN}-catalog/manual-needed.md \
  --selected-only --assign-ids
uv run python -m papers_library_pipeline.sync_manifest
uv run python -m papers_library_pipeline.export_excel
```

Copy `scripts/domain_config.example.json` → `{ROOT}/domain_config.json` (usually the **current project dir**; `"root": "."`).  
Optional seeds: `scripts/seed_works.example.json` → `{DOMAIN}-candidates/seed_works.json`.

| Module | Use |
|--------|-----|
| `run_harvest` | `--theme` (one theme → shards) / `--integrate` / `--seeds-only`. **Not** for refs. Timeout ≥ **2 min per `--theme`** |
| `expand_refs` | `--next` or `--doi` — **one paper per call**; separate from harvest |
| `pdf_fetch` | search/download PDF (`--assign-ids`); Sci-Hub probes once then prefers last-known-good mirror |
| `source_health` | Read/write `{DOMAIN}-catalog/source-health.json` |
| `sync_manifest` | Rebuild catalog from PDF disk (`--include-md` optional) |
| `export_excel` | Write `literature.xlsx` |

`pdf_fetch` order: OA → preferred Sci-Hub mirror (then other mirrors) → manual.  
`ai_*_threshold` in config are **triage hints** (script-only / hybrid), not enforced by download scripts.

## Anti-patterns

- Converting PDFs to Markdown or calling OCR from this skill
- Building `{DOMAIN}-web/` here
- Downloading without `local_id`
- Skipping Excel export before handoff to B
- Starting Stage 2 triage writes without asking Full AI / Script-only / Hybrid
- Rewriting OpenAlex/Crossref/`pdf_fetch` clients without need
