# papers-to-knowledge-base

[中文说明](README.zh-CN.md)

Turn a research topic into a **local literature library**, and optionally a **browsable static knowledge site**.

Made for people who use AI coding agents (Cursor, Claude Code, Codex, …). After you install these Agent Skills, tell the agent your domain and goal; it can search papers, download PDFs, export an Excel triage list, then (optionally) convert to Markdown and build a static HTML tutorial site.

## What problem this solves

When surveying a specialty, you often hit:

- Papers scattered across OpenAlex / Crossref / publishers — hard to download and number consistently  
- Accept / reject decisions living in your head — no durable Excel list  
- Humans need PDFs; agents need Markdown to author a site; scans may need OCR  
- You want an **offline HTML site**, not a chat transcript  

This repo packages that workflow as reusable skills + scripts.

## What you can do

| Capability | What it means |
|------------|----------------|
| Intake before bulk work | Choose library-only, site-only, or full A→B; no mass download/convert until you confirm |
| Harvest | OpenAlex + Crossref search, dedupe, script scoring; parallel theme shards when the host has subagents |
| Triage | AI/human review; `accepted` flags and reasons; parallel review batches then merge in the parent |
| PDF download | Fetch by DOI when possible; failures go to `manual-needed.md` |
| Excel catalog | `{domain}-catalog/literature.xlsx` (id, title, DOI, scores, accept, PDF status, …) |
| PDF→Markdown | MarkItDown by default; optional PaddleOCR MCP for scans |
| Static knowledge site | Glossary + chapters + plain HTML (no `npm install` required to read) |

**Out of scope:** inventing your scientific conclusions; publishing local PDF paths; skipping your final accept/reject confirmation.

## Three ways to use it

| Mode | When | You get |
|------|------|---------|
| **Library only (A)** | PDFs + Excel are enough | `{domain}-pdf/`, `literature.xlsx`, … |
| **Site only (B)** | You already have accepted PDFs (+ list) | `{domain}-md/` + `{domain}-web/` |
| **Full (A→B)** | Search through to a site | A first, then B after you confirm Excel |

Example prompts:

- *“Use papers-to-knowledge-base for a solid-electrolyte library — PDFs and Excel only.”*  
- *“PDFs are ready; use papers-knowledge-site to build a Chinese knowledge site.”*

## What’s in the repo

| Folder | Role |
|--------|------|
| [`skills/papers-to-knowledge-base`](skills/papers-to-knowledge-base/) | Orchestrator: intake, bind vars, route to A / B |
| [`skills/papers-library-pipeline`](skills/papers-library-pipeline/) | A: harvest → triage → download → Excel |
| [`skills/papers-knowledge-site`](skills/papers-knowledge-site/) | B: PDF→MD → static site |

| Goal | Install these folders |
|------|------------------------|
| Full pipeline | all three |
| Library only | orchestrator + `papers-library-pipeline` |
| Site only | orchestrator + `papers-knowledge-site` |

## Install (project skills — recommended)

Put the skill folders into **this project’s** skills directory (not the user home directory).

| Host | Path under the project |
|------|------------------------|
| Cursor | `.cursor/skills/<name>/` |
| Claude Code | `.claude/skills/<name>/` |
| Codex | `.agents/skills/<name>/` |
| OpenCode | `.opencode/skills/<name>/` |
| Pi | `.pi/skills/<name>/` |

**What to install:** copy (or move) the chosen folders from this repo’s [`skills/`](skills/) into that path. Each folder must contain `SKILL.md`.

Example (Cursor, full pipeline) — after you already have this repo open / checked out:

```text
.cursor/skills/papers-to-knowledge-base/
.cursor/skills/papers-library-pipeline/
.cursor/skills/papers-knowledge-site/
```

**For agents:** install into the **current project** skills path above. Do **not** install into `~/.cursor/skills` (or other home paths) unless the user explicitly asks for a personal/global install. Do **not** clone the whole repo into a temp folder just to re-copy — if the repo is already the workspace, place/copy folders from `skills/` into `.cursor/skills/` (or the matching host path). Prefer **copy** of the skill folders so the project is self-contained; a symlink/junction is fine only when the user asks to keep a single shared checkout.

Reload the agent after installing. Details: [`skills/papers-to-knowledge-base/references/install-hosts.md`](skills/papers-to-knowledge-base/references/install-hosts.md).

### Optional: personal (all projects)

Only if the user wants skills in every project: use the host’s **personal** skills dir (`~/.cursor/skills/`, `~/.claude/skills/`, …) with the same folder names. Default remains **project-local**.

## Python tooling

Scripts use a [uv](https://docs.astral.sh/uv/) workspace at **this repo root** (where `pyproject.toml` and `skills/*/scripts` live). From that root:

```powershell
uv sync --group dev
uv run python -m papers_library_pipeline.run_harvest
uv run python -m papers_knowledge_site.pdf_to_md -h
```

Python **3.12** or **3.13**. PDF names: `{id}.{title}.pdf`.

### Secrets (`.env`)

At the repo root (do **not** commit `.env`):

```powershell
Copy-Item .env.example .env
# Edit .env:
#   OPENALEX_API_KEY=...                 # https://openalex.org/settings/api
#   PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN=...  # https://aistudio.baidu.com/paddleocr
```

Harvest scripts load `.env` automatically. The PaddleOCR MCP template uses `uvx --env-file .env` so the token stays out of `mcp.json`.

## License

MIT — see [LICENSE](LICENSE).
