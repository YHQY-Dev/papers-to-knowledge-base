# papers-to-knowledge-base

[中文说明](README.zh-CN.md)

**Orchestrator Agent Skill** for academic papers → local library and/or static HTML knowledge site. Owns **two-phase intake** and routes to sibling skills.

Compatible with **Cursor**, **Claude Code**, **Codex**, **OpenCode**, **Pi**, and any host that follows the [Agent Skills](https://agentskills.io) `SKILL.md` layout.

## Skill family

| Skill folder | Role |
|--------------|------|
| `papers-to-knowledge-base` | Intake (Q0 + Phase 1/2) + routing |
| `papers-library-pipeline` | **A** — harvest, triage, PDF download, Excel catalog |
| `papers-knowledge-site` | **B** — PDF→Markdown, optional PaddleOCR, static HTML site |

## Q0 / Phase 1 behavior (summary)

- **Q0:** library only (A) / site only (B) / full (A→B)  
- **Phase 1 Q1–Q3** always (domain, `{N}`, `{ROOT}`) — **site-only may skip `{N}`** if keeping an existing PDF/Excel set  
- **Q4 `{LANG}` + Q5 PaddleOCR** only for **B** or **A→B**  
- **Library-only skips LANG and OCR questions**  
- No harvest/download/convert/site until the user confirms the intake summary  

Full scripts: [references/intake.md](references/intake.md).

## Install matrix

| Goal | Skills to install |
|------|-------------------|
| Full | all three folders |
| Library-only | this orchestrator + `papers-library-pipeline` |
| Site-only | this orchestrator + `papers-knowledge-site` |

Multi-host paths: [references/install-hosts.md](references/install-hosts.md). See also the repo root [README](../../README.md).

## Optional PaddleOCR MCP (stage B)

Copy [`mcp/paddleocr.mcp.json.example`](mcp/paddleocr.mcp.json.example) into the host MCP config and set `PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN`. Without a token, B uses MarkItDown only.

## Layout

```text
papers-to-knowledge-base/
  SKILL.md
  README.md / README.zh-CN.md
  mcp/paddleocr.mcp.json.example
  references/
    intake.md
    install-hosts.md
```

## License

MIT. Scripts and stage logic live in the sibling skill folders.
