# Parallel subagents (stage A)

Use **only if the host can run subagents** (e.g. Cursor Task / Claude Code Task). If not, stay single-threaded.

## When to parallelize

Independent shards of **search** or **review/scoring** — not steps that share a write lock.

| Parallel OK | Keep sequential (parent or one agent) |
|-------------|----------------------------------------|
| Theme / query shards for harvest | Merging into `candidates.json` |
| Batches of AI triage / `ai_score` / `accepted` + `reason` | Assigning `local_id` + `fetch-batch` |
| Reading disjoint candidate slices for review | Final `export_excel` / checklist |

## Suggested fan-out

1. **Parent** loads config: `{DOMAIN}`, `{ROOT}`, `{N}`, `{THEMES}`, `domain_config.json`.
2. Split work into **2–N shards** (by theme, year band, or candidate index ranges). One subagent per shard.
3. Each subagent returns a **structured result** (JSON list of records or review patches) — not a half-written shared file unless the parent assigned exclusive paths.
4. **Parent merges** (dedupe by DOI/title), writes `candidates.json`, then runs download + Excel **once**.

### Harvest shard prompt (template)

- Goal: find candidates for theme(s) `…` under scope `…`
- Tools: OpenAlex/Crossref via `papers_library_pipeline` or equivalent HTTP
- Output: JSON array of records (`title`, `doi`, `year`, `type`, `abstract` snippet, `script_score` if computed)
- Do **not** download PDFs; do **not** assign `local_id`; do **not** edit Excel

### Review shard prompt (template)

- Input: candidate slice (ids or DOI list) + acceptance criteria / `{THEMES}`
- Output: per item `ai_score`, `accepted`/`selected`, `decision`, `reason` (and optional note path under `ai-reviews/`)
- Do **not** run `fetch-batch`; do **not** renumber `local_id`

## Merge rules

- Dedupe with existing `record_key` logic (DOI → ISBN → normalized title)
- Prefer higher `script_score` / richer abstract when merging duplicates
- Only after all review shards return: set `accepted`, then `--assign-ids` + `--selected-only` download
- One writer for `candidates.json` and `literature.xlsx` (the parent)

## Caps

- Prefer **few wide shards** (e.g. 3–8) over dozens of tiny agents
- If `{N}` is small or themes are one string, parallel subagents are optional — skip
