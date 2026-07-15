---
name: papers-to-knowledge-base
description: >-
  Use when the user wants a domain literature library, paper download pipeline,
  Excel catalog, and/or static knowledge/教程站 from academic papers (文献库,
  打分下载, MarkItDown 知识库, PaddleOCR, “搜论文并做成网站”, library-only or
  site-only or full A→B)—not for general web scraping or unrelated site redesigns.
  Orchestrates intake then routes to papers-library-pipeline and/or
  papers-knowledge-site.
license: MIT
compatibility: Agent Skills hosts (Cursor, Claude Code, Codex, OpenCode, Pi)
---

# Papers → Knowledge Base (orchestrator)

Two-phase **intake** + **routing** across sibling skills:

| Skill | Role |
|-------|------|
| **papers-to-knowledge-base** (this) | Intake gate, bind variables, choose A / B / A→B |
| **papers-library-pipeline** | A: harvest → triage → PDF + Excel. No MD/site |
| **papers-knowledge-site** | B: PDF→MD (MarkItDown / optional PaddleOCR) → static HTML |

Human docs: [README.md](README.md) · [README.zh-CN.md](README.zh-CN.md) · [references/install-hosts.md](references/install-hosts.md) · [references/intake.md](references/intake.md).

## Hard gate (mandatory)

**Before any harvest, download, convert, or site work:** follow **[references/intake.md](references/intake.md)** end-to-end.

1. **Q0** routing: A only / B only / A→B  
2. **Phase 1** Q1–Q3 always (site-only may skip `{N}` if keeping existing set); **Q4 `{LANG}` + Q5 PaddleOCR only if B or A→B**  
3. **Library-only (A)** skips Q4–Q5  
4. Offer **Phase 2** (five optional questions)  
5. Persist `{ROOT}/specs/intake.md`  
6. Present summary → **user confirms**

**FORBIDDEN** until confirmation: harvest / download / convert / site.

## REQUIRED SUB-SKILLS

**REQUIRED SUB-SKILL:** Use `papers-library-pipeline` when running stage A.  
**REQUIRED SUB-SKILL:** Use `papers-knowledge-site` when running stage B.

Load and follow those skills’ `SKILL.md` after intake confirmation. Do not reimplement their pipelines here.

When handing off to **A**, if the host supports subagents, prefer **parallel** harvest/review shards as described in `papers-library-pipeline` ([parallel-subagents.md](../papers-library-pipeline/references/parallel-subagents.md)).

## Routing

| Intent | Intake | Action |
|--------|--------|--------|
| Library only (A) | Phase 1: Q1–Q3 (+ Phase 2 as needed); skip LANG/OCR | **REQUIRED** `papers-library-pipeline` → stop |
| Site only (B) | Phase 1 including LANG + OCR (PDFs already present) | **REQUIRED** `papers-knowledge-site` |
| Full (A→B) | Full Phase 1 (incl. LANG + OCR) | A → user confirms Excel/acceptance → B |

Boundary: humans read **PDFs** from A; Markdown is mainly for **AI** authoring in B. OCR / MarkItDown live **only in B**.

## Install matrix

| Goal | Install these skill folders |
|------|-----------------------------|
| **Full** pipeline | `papers-to-knowledge-base` + `papers-library-pipeline` + `papers-knowledge-site` |
| **Library-only** | orchestrator + `papers-library-pipeline` |
| **Site-only** | orchestrator + `papers-knowledge-site` (minimum B; A optional if PDFs already exist) |

Install into the **current project** skills dir by placing folders from repo `skills/` there (e.g. Cursor: `.cursor/skills/<name>/`). See [install-hosts.md](references/install-hosts.md) / repo README. Do not default to personal `~/…/skills`.

## Optional PaddleOCR MCP (for B)

Template: [`mcp/paddleocr.mcp.json.example`](mcp/paddleocr.mcp.json.example)  
Wiring details live with B (`papers-knowledge-site` references). Token: [AI Studio PaddleOCR](https://aistudio.baidu.com/paddleocr). Missing token → MarkItDown only; never block.

## When NOT to use

- Only a few ad-hoc PDFs with no library or site pipeline  
- Unrelated marketing / CMS work  
- Pure code refactor with no literature/KB intent  

## After intake (variable contract)

| Var | Meaning |
|-----|---------|
| `{ROUTE}` | `A` \| `B` \| `A→B` |
| `{DOMAIN}` | slug |
| `{ROOT}` | asset root (**default: cwd** / `"."` in domain_config) |
| `{N}` | target count (may be “existing” for B-only) |
| `{THEMES}` / `{SCOPE_MODE}` | themes + narrow/broad |
| `{LANG}` | site language (B / A→B only) |
| `{OCR}` | paddleocr-mcp vs markitdown-only (B / A→B only) |

Then hand off to the required sub-skill(s) with these bindings.
