# Intake scripts (hard gate)

**Audience:** agents running `papers-to-knowledge-base`.

**Hard gate:** Do **not** run harvest, PDF download, PDF→Markdown, OCR, or static site generation until:

1. Q0 + applicable Phase 1 questions are answered (or already known and confirmed),
2. Phase 2 has been offered (or user declines optional details),
3. You present an **intake summary**, and
4. The user **explicitly confirms**.

Until then, **FORBIDDEN:** harvest / download / convert / site work.

Ask **one question at a time**. Skip any item the user already answered clearly in the current thread.

---

## Q0 — Routing (always first)

Ask which path they want:

| Choice | Label | Meaning |
|--------|-------|---------|
| **A only** | Library only | Harvest → triage → PDF + Excel catalog. Stop. No MD/site. |
| **B only** | Site only | PDFs (and acceptance list) already exist → MD + static HTML site. |
| **A→B** | Full pipeline | Run A, user confirms Excel/acceptance, then B. |

Example prompt:

> Do you want **(A) library only** (PDF + Excel), **(B) site only** (you already have PDFs), or **(A→B) full pipeline** (library then knowledge site)?

Bind routing: `{ROUTE}` ∈ `A` | `B` | `A→B`.

**Effect on Phase 1:**

- **A only** → ask Q1–Q3 only; **skip Q4 and Q5** (`{LANG}`, PaddleOCR).
- **B only** or **A→B** → ask Q1–Q3, then **Q4 and Q5**.

---

## Phase 1 — required

### Q1 — Domain / scope

Ask whether this is a **narrow specialty** or a **broad survey**, and get concrete topic wording.

Bind:

| Var | Meaning |
|-----|---------|
| `{SCOPE_MODE}` | `narrow` \| `broad` |
| `{THEMES}` | search / curriculum themes (list) |
| `{DOMAIN}` | filesystem slug (e.g. `battery`) |

Example:

> Is this a **narrow specialty** or a **broad survey**? Give the exact topic wording and a short slug for folders (e.g. `solid-electrolyte`).

### Q2 — Target paper count `{N}`

Default **100+** if user is unsure.

**Site-only caveat:** If `{ROUTE}` is **B only**, and accepted PDFs / Excel / manifest already exist under `{ROOT}`, you **may skip** Q2 when the user declines expansion (keep existing set). Still record `{N}` as “existing set” or the count they state.

Example:

> Roughly how many papers should we aim for? Default is **100+**. (Site-only: say “keep existing” if you do not want more downloads.)

### Q3 — Output root `{ROOT}`

Absolute path for `domain_config.json`, `{DOMAIN}-pdf/`, catalog, specs, etc.

Example:

> Where should assets live? Give an absolute root path `{ROOT}` (e.g. `D:/work/battery-kb`).

### Q4 — Primary language `{LANG}`

**ONLY if** `{ROUTE}` is **B** or **A→B**.  
**Skip entirely for A only (library-only).**

Example:

> Primary language for the knowledge site / chapters? (`zh`, `en`, …) → `{LANG}`

### Q5 — PaddleOCR MCP

**ONLY if** `{ROUTE}` is **B** or **A→B**.  
**Skip entirely for A only (library-only).**

Ask whether an AI Studio PaddleOCR token is already in the repo-root `.env` (`PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN`) and wired via host MCP.

- If **not**: offer to help apply / wire [AI Studio PaddleOCR](https://aistudio.baidu.com/paddleocr) (currently free after registration): fill `.env` from `.env.example`, then merge [`../mcp/paddleocr.mcp.json.example`](../mcp/paddleocr.mcp.json.example) (same under `papers-knowledge-site/mcp/`).
- If user **declines** or token unavailable → B uses **MarkItDown only**. Never block the pipeline on OCR.

Bind: `{OCR}` ∈ `paddleocr-mcp` | `markitdown-only` (or equivalent).

Example:

> For scanned PDFs, do you already have a PaddleOCR MCP token configured? If not, I can help set one up from AI Studio; otherwise we will convert with MarkItDown only.

---

## Phase 2 — optional details (offer all five)

After Phase 1, offer these (defaults OK if user skips). Ask one at a time or as a short checklist they can answer partially.

1. Prefer **reviews/books** vs many application papers?
2. Explicit **exclude** policy (e.g. methods-only, no application case studies)?
3. Confirm **library only vs must build static site** (should match Q0; use to correct routing and whether Q4–Q5 apply)?
4. Seed **must-have DOIs/ISBNs**?
5. **Bilingual** site or primary language only? (Relevant when B or A→B; for A-only, note “N/A until site” or skip.)

Bind extras into `{SCOPE}` / notes as needed for A triage and B authoring.

---

## Intake summary → user confirmation

Before any heavy work, present a short summary, for example:

```text
Route: {ROUTE}
Domain: {DOMAIN} ({SCOPE_MODE})
Themes: {THEMES}
N: {N}
ROOT: {ROOT}
LANG: {LANG}          # omit line if A only
OCR: {OCR}            # omit line if A only
Phase 2 notes: …
```

Ask: **Confirm to proceed?**  
Only after an explicit yes → persist files and invoke the required sub-skill(s).

---

## Persistence

### `{ROOT}/specs/intake.md`

Create `{ROOT}/specs/` if needed. Write a Q&A summary using at least these headings:

```markdown
# Intake — {DOMAIN}

## Routing
- Route: …
- Confirmed: yes/no + date

## Phase 1
- SCOPE_MODE / THEMES / DOMAIN:
- N:
- ROOT:
- LANG:          # "n/a (library-only)" when A only
- OCR:           # "n/a (library-only)" when A only

## Phase 2
- Reviews/books preference:
- Exclude policy:
- Library vs site:
- Seed DOIs/ISBNs:
- Bilingual:

## Variables
| Var | Value |
|-----|-------|
| DOMAIN | |
| ROOT | |
| N | |
| THEMES | |
| SCOPE_MODE | |
| LANG | |
| OCR | |
| ROUTE | |
```

### `domain_config.json`

Generate or update fields needed by A scripts under `{ROOT}/domain_config.json` (from A’s `domain_config.example.json`) when route includes A. For B-only, still ensure `{ROOT}` / `{DOMAIN}` paths are clear for convert + site.

---

## After confirmation — routing actions

| `{ROUTE}` | Action |
|-----------|--------|
| **A only** | **REQUIRED SUB-SKILL:** `papers-library-pipeline` → stop after Excel/PDF |
| **B only** | **REQUIRED SUB-SKILL:** `papers-knowledge-site` |
| **A→B** | **REQUIRED:** `papers-library-pipeline` → user confirms Excel/acceptance → **REQUIRED:** `papers-knowledge-site` |

---

## FORBIDDEN before confirmation

- `run_harvest` / OpenAlex / Crossref bulk harvest  
- `pdf_fetch` / batch PDF download  
- PDF→MD / MarkItDown / PaddleOCR conversion  
- Building `{DOMAIN}-web/` or rewriting the static site  
- Mass triage that mutates acceptance at scale as a substitute for “starting work”

Allowed before confirmation: clarifying questions, reading existing `{ROOT}` layout, summarizing what the user already said.
