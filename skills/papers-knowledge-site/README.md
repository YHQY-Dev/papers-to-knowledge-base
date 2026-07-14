# papers-knowledge-site

[中文说明](README.zh-CN.md)

**Agent Skill (stage B)** — convert accepted academic PDFs to Markdown and build a static HTML knowledge site. No bulk harvest or PDF download.

Compatible with **Cursor**, **Claude Code**, **Codex**, **OpenCode**, **Pi**, and hosts that follow the [Agent Skills](https://agentskills.io) `SKILL.md` layout.

Part of the `papers-to-knowledge-base` family:

| Skill | Role |
|-------|------|
| `papers-to-knowledge-base` | Intake + routing |
| `papers-library-pipeline` | A: harvest → PDF → Excel |
| **`papers-knowledge-site`** | **B: PDF→MD → static site** |

## What you get

| Piece | Role |
|-------|------|
| `SKILL.md` | Agent instructions for convert + site |
| `scripts/papers_knowledge_site/` | MarkItDown convert, image extract, citation clues |
| `mcp/paddleocr.mcp.json.example` | **Optional** PaddleOCR-VL MCP for scanned PDFs |
| `references/` | Static site rules, OCR notes, site checklist |

**Default PDF→Markdown:** [MarkItDown](https://github.com/microsoft/markitdown).  
**Optional OCR:** PaddleOCR-VL MCP — token from [AI Studio PaddleOCR](https://aistudio.baidu.com/paddleocr). If unset, stay on MarkItDown.

**Humans read PDFs.** Markdown is mainly for AI authoring of the site.

## Prerequisites

- Accepted PDFs under `{DOMAIN}-pdf/`
- Acceptance list (`{DOMAIN}-catalog/literature.xlsx` and/or manifest)
- `{LANG}` and OCR preference (from orchestrator intake, or ask if alone)

## Install

Link into **the skills directory of the agent you use** only.  
See the [repo README](../../README.md) — do not install into every host at once.  
Prefer also linking the orchestrator for intake when starting from scratch.

## Convert + site (summary)

```text
PDFs + acceptance → Convert (PaddleOCR MCP? else MarkItDown)
→ Glossary → Chapters → Static HTML → Checklist
```

```bash
# from repo root (shared uv workspace with stage A)
uv sync
uv run python -m papers_knowledge_site.pdf_to_md batch --pdf-dir {ROOT}/FIELD-pdf --md-dir {ROOT}/FIELD-md
```

Tell the agent: *“Use papers-knowledge-site to convert these PDFs and build the static knowledge site.”*

Site layout: [references/static-html-site.md](references/static-html-site.md).  
Acceptance: [references/checklist.md](references/checklist.md).

## Optional PaddleOCR MCP

1. Set `PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN=` in the repo-root `.env` (do not commit `.env`).  
2. Merge `mcp/paddleocr.mcp.json.example` into the host MCP config (`uvx --env-file .env`).  
3. See [references/paddleocr-mcp.md](references/paddleocr-mcp.md).

| Host | Typical MCP config |
|------|--------------------|
| Cursor | `~/.cursor/mcp.json` → `mcpServers` |
| Claude Code | `~/.claude.json` or project `.mcp.json` |
| Codex | `~/.codex/config.toml` → `[mcp_servers.…]` |
| OpenCode / Pi | Host MCP / tools settings |

Without a token, conversion stays on MarkItDown.

## Layout

```text
papers-knowledge-site/
  SKILL.md
  README.md / README.zh-CN.md
  mcp/paddleocr.mcp.json.example
  references/
    static-html-site.md
    paddleocr-mcp.md
    checklist.md
  scripts/
    pyproject.toml
    papers_knowledge_site/   # Python package
```

## License / notes

Public sites must cite DOI/OA only — do not publish links into local `*-pdf/` / `*-md/` trees.  
For harvest/download/Excel, use `papers-library-pipeline`.
