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

Three installable Agent Skills (link them into **the one agent you use**):

| Folder | Role |
|--------|------|
| [`skills/papers-to-knowledge-base`](skills/papers-to-knowledge-base/) | Orchestrator: intake, bind vars, route to A / B |
| [`skills/papers-library-pipeline`](skills/papers-library-pipeline/) | A: harvest → triage → download → Excel |
| [`skills/papers-knowledge-site`](skills/papers-knowledge-site/) | B: PDF→MD → static site |

Scripts share one [uv](https://docs.astral.sh/uv/) workspace at the repo root (independent of which agent you linked):

```powershell
uv sync --group dev
uv run python -m papers_library_pipeline.run_harvest
uv run python -m papers_knowledge_site.pdf_to_md -h
```

Python **3.12** or **3.13**. PDF names: `{id}.{title}.pdf`.

## Install skills (per agent)

| Goal | Link these under `skills/` |
|------|----------------------------|
| Full pipeline | all three |
| Library only | orchestrator + `papers-library-pipeline` |
| Site only | orchestrator + `papers-knowledge-site` |

**Install only for the agent you use** — not every host at once. Set `REPO` to your clone root (the folder that contains `skills/`), then use one section below.

### Cursor

Personal: `~/.cursor/skills/<name>/` · Project: `.cursor/skills/<name>/`

```powershell
$REPO = "D:\path\to\papers-to-knowledge-base"
$dest = "$env:USERPROFILE\.cursor\skills"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
foreach ($name in @(
  "papers-to-knowledge-base",
  "papers-library-pipeline",
  "papers-knowledge-site"
)) {
  New-Item -ItemType Junction -Force -Path "$dest\$name" -Target "$REPO\skills\$name" | Out-Null
}
```

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.cursor/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.cursor/skills/$name
done
```

### Claude Code

Personal: `~/.claude/skills/<name>/` · Project: `.claude/skills/<name>/`

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.claude/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.claude/skills/$name
done
```

### Codex

Personal: `~/.agents/skills/<name>/` · Project: `.agents/skills/<name>/`

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.agents/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.agents/skills/$name
done
```

### OpenCode

Personal: `~/.config/opencode/skills/<name>/` · Project: `.opencode/skills/<name>/`

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.config/opencode/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.config/opencode/skills/$name
done
```

### Pi

Personal: `~/.pi/agent/skills/<name>/` · Project: `.pi/skills/<name>/`

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.pi/agent/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.pi/agent/skills/$name
done
```

Reload that agent afterward. MCP and project paths: [`skills/papers-to-knowledge-base/references/install-hosts.md`](skills/papers-to-knowledge-base/references/install-hosts.md).

## License

MIT — see [LICENSE](LICENSE).
