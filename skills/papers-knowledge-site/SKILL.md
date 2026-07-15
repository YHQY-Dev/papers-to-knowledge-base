---
name: papers-knowledge-site
description: >-
  Use when the user already has accepted PDFs (and Excel/manifest) and wants
  PDF→Markdown conversion, optional PaddleOCR, glossary/chapters, or a static
  HTML knowledge/教程站 (知识站, MarkItDown, PaddleOCR, “把论文做成网站”)—not for
  bulk paper discovery, harvest, or PDF download (use papers-library-pipeline).
license: MIT
compatibility: Agent Skills hosts (Cursor, Claude Code, Codex, OpenCode, Pi)
---

# Papers → Static Knowledge Site

Stage **B** only: convert accepted PDFs to Markdown, then build a static HTML site.  
Humans read **PDFs**; Markdown exists mainly so **AI** can author the site.

Sibling skills: orchestrator `papers-to-knowledge-base`; library stage A `papers-library-pipeline`.

Human docs: [README.md](README.md) · [README.zh-CN.md](README.zh-CN.md).

## When NOT to use

- Bulk harvest / download / scoring / Excel export → **REQUIRED** `papers-library-pipeline`
- Full A→B from scratch without intake → **REQUIRED** `papers-to-knowledge-base` first
- Unrelated marketing/CMS site work

## Prerequisites (refuse or ask if missing)

| Var / input | Meaning |
|-------------|---------|
| Accepted PDFs | `{DOMAIN}-pdf/{local_id}.{title}.pdf` |
| Acceptance list | Excel (`literature.xlsx`) and/or manifest / candidates with accepted rows |
| `{DOMAIN}` | slug |
| `{ROOT}` | asset root (**default: current project dir**) |
| `{LANG}` | primary site language |
| OCR preference | PaddleOCR token configured? else MarkItDown only |

If invoked alone (not via orchestrator), require the above or refuse heavy convert/site work until the user confirms.

**Hard rule:** no bulk paper discovery, OpenAlex/Crossref harvest, or PDF download in this skill. Missing PDFs → hand back to A or `manual-needed`.

## Critical rules

1. Parameterize `{DOMAIN}` / `{ROOT}` / `{LANG}`; never hard-code a single project path.
2. Convert waterfall: **PaddleOCR MCP if ready and needed → else MarkItDown** (`pdf_to_md`). Never block on a missing OCR token.
3. Public site: static HTML + KaTeX CDN; DOI/OA cites only; plain `Å`; no local `*-pdf/` / `*-md/` links.
4. Lock glossary term ids before parallel chapter agents.
5. Reuse `scripts/papers_knowledge_site/` — do not rewrite MarkItDown / image extract helpers.

## Optional PaddleOCR MCP

Template: [`mcp/paddleocr.mcp.json.example`](mcp/paddleocr.mcp.json.example)  
Details: [references/paddleocr-mcp.md](references/paddleocr-mcp.md)

1. User applies for token at https://aistudio.baidu.com/paddleocr  
2. Put token in repo-root `.env` as `PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN=`; merge `mcp/paddleocr.mcp.json.example` into host MCP (loads `.env` via `uvx --env-file`)  
3. If MCP not configured / fails → **MarkItDown only**

Agent tool (when ready): `paddleocr_vl` with absolute PDF path, `file_type="pdf"`.  
Then `write_md_bundle(pdf, out_dir, text, converter="paddleocr-vl")`.

## Bundled code

From the **repo root** (shared uv workspace with stage A):

| Module | Use |
|--------|-----|
| `pdf_to_md` | MarkItDown default; `write_md_bundle` after PaddleOCR |
| `extract_pdf_images` | Embedded figures → `{id}/imgs/` (PyMuPDF) |
| `citation_extract` | DOI/refs from MD (clues only; no download) |

```bash
uv sync
# default convert (no OCR MCP needed):
uv run python -m papers_knowledge_site.pdf_to_md batch --pdf-dir {ROOT}/{DOMAIN}-pdf --md-dir {ROOT}/{DOMAIN}-md
uv run python -m papers_knowledge_site.pdf_to_md convert path/to/id.name.pdf --out-dir {ROOT}/{DOMAIN}-md/id
uv run python -m papers_knowledge_site.citation_extract {ROOT}/{DOMAIN}-md/id/content.md --id id -o {ROOT}/{DOMAIN}-catalog/citations/id.json
```

## Pipeline

```text
Prerequisites → Convert (PaddleOCR MCP if ready else MarkItDown)
→ Glossary lock → Chapters → Static HTML → Checklist
```

| Stage | Do |
|-------|----|
| Convert | OCR MCP if configured/needed, else `pdf_to_md` → `{DOMAIN}-md/{id}/content.md` |
| Glossary | Lock term `id`s; bidirectional chapter ↔ term links |
| Site | `{DOMAIN}-web/` — [static-html-site.md](references/static-html-site.md) |
| Done | [checklist.md](references/checklist.md) |

**Parallel OK:** converts, chapter drafts after glossary schema. **Serial:** prerequisites, glossary ids, site shell.

## Directory contract

```text
{ROOT}/
  {DOMAIN}-pdf/{local_id}.{title}.pdf  # input (from A or user)
  {DOMAIN}-catalog/literature.xlsx     # acceptance list (typical)
  {DOMAIN}-md/{local_id}/content.md    # + convert_meta.json, imgs/
  {DOMAIN}-web/                        # static site output
```

## Anti-patterns

- Harvesting or downloading papers inside this skill
- Requiring PaddleOCR for every run (MarkItDown must remain enough)
- Committing AI Studio tokens
- npm-only reader path; dumping whole MD books into the public site
- Publishing links into local `*-pdf/` / `*-md/` trees
