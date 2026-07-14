# Install on multiple AI coding hosts

This family follows the open **[Agent Skills](https://agentskills.io)** layout: each skill is a folder containing `SKILL.md` (plus optional `scripts/`, `references/`, `mcp/`).

Install **one folder per skill**. Hosts differ mainly in **where they scan for skills** and **where MCP servers are declared**.

## Skill folder names (all three)

| Folder | Role |
|--------|------|
| `papers-to-knowledge-base` | Orchestrator (intake + routing) |
| `papers-library-pipeline` | Stage A (library / PDF / Excel) |
| `papers-knowledge-site` | Stage B (MD / OCR / static site) |

**Install matrix:** full = all three; library-only = orchestrator + A; site-only = orchestrator + B.

## Recommended install (works everywhere)

**Option A — personal (all projects)**  
Copy or symlink each needed folder into a user skills root your host already scans:

| Host | Personal / global path pattern |
|------|--------------------------------|
| Cursor | `~/.cursor/skills/<skill-name>/` |
| Claude Code | `~/.claude/skills/<skill-name>/` |
| Codex | `~/.agents/skills/<skill-name>/` (also legacy `~/.codex/skills/`) |
| OpenCode | `~/.config/opencode/skills/<skill-name>/` **or** `~/.agents/skills/` / `~/.claude/skills/` |
| Pi | `~/.pi/agent/skills/<skill-name>/` **or** `~/.agents/skills/` |
| Generic / shared | `~/.agents/skills/<skill-name>/` |

Replace `<skill-name>` with each of:

- `papers-to-knowledge-base`
- `papers-library-pipeline`
- `papers-knowledge-site`

**Option B — project (shared with repo)**  
Copy or symlink into the repo (hosts walk up from cwd):

| Host | Project path pattern |
|------|----------------------|
| Cursor | `.cursor/skills/<skill-name>/` |
| Claude Code | `.claude/skills/<skill-name>/` |
| Codex / Pi / OpenCode (shared) | `.agents/skills/<skill-name>/` |
| OpenCode-native | `.opencode/skills/<skill-name>/` |
| Pi-native | `.pi/skills/<skill-name>/` |

**Windows (PowerShell) — full set:**

```powershell
$root = "D:\software\SAS\Skill\skills"   # or your clone path\skills
$hosts = @(
  "$env:USERPROFILE\.agents\skills",
  "$env:USERPROFILE\.claude\skills",
  "$env:USERPROFILE\.cursor\skills",
  "$env:USERPROFILE\.pi\agent\skills",
  "$env:USERPROFILE\.config\opencode\skills"
)
foreach ($name in @(
  "papers-to-knowledge-base",
  "papers-library-pipeline",
  "papers-knowledge-site"
)) {
  $src = Join-Path $root $name
  foreach ($h in $hosts) {
    New-Item -ItemType Directory -Force -Path $h | Out-Null
    New-Item -ItemType Junction -Force -Path (Join-Path $h $name) -Target $src | Out-Null
  }
}
```

**Unix — full set:**

```bash
SRC=/absolute/path/to/repo/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  mkdir -p ~/.agents/skills ~/.claude/skills ~/.cursor/skills \
           ~/.pi/agent/skills ~/.config/opencode/skills
  ln -sfn "$SRC/$name" ~/.agents/skills/$name
  ln -sfn "$SRC/$name" ~/.claude/skills/$name
  ln -sfn "$SRC/$name" ~/.cursor/skills/$name
  ln -sfn "$SRC/$name" ~/.pi/agent/skills/$name
  ln -sfn "$SRC/$name" ~/.config/opencode/skills/$name
done
```

> Tip: Installing once under `~/.agents/skills/` covers Codex, OpenCode, and Pi for many setups. Add junctions for Cursor (`~/.cursor/skills`) and Claude Code (`~/.claude/skills`) if those hosts do not also read `.agents`.

Restart / reload the agent after install so skill metadata is rediscovered.

## How agents should load these skills

| Host | How discovery works |
|------|---------------------|
| Cursor | Auto from `~/.cursor/skills` / project `.cursor/skills`; follow matching `SKILL.md` |
| Claude Code | Auto from `~/.claude/skills` / `.claude/skills`; may invoke as `/papers-to-knowledge-base` etc. |
| Codex | Progressive disclosure from `.agents/skills` / `~/.agents/skills` |
| OpenCode | Native `skill` tool lists name+description; loads on demand |
| Pi | Lists skills; `/skill:papers-to-knowledge-base` or auto-load |

**Tool names in `SKILL.md` are host-agnostic intent.** Map them to the host:

| Intent in skill | Typical host tools |
|-----------------|-------------------|
| Run shell / Python modules | Bash / Shell / terminal |
| Edit files | Write / Edit / apply_patch |
| Read files | Read |
| Optional OCR MCP | Host MCP bridge (`paddleocr_vl`) |
| Sub-skills A/B | Load sibling skill `SKILL.md` by name |

## Optional PaddleOCR MCP (stage B; all hosts)

1. Get a token: https://aistudio.baidu.com/paddleocr  
2. Merge `papers-to-knowledge-base/mcp/paddleocr.mcp.json.example` (or the copy under `papers-knowledge-site/mcp/`) into the host MCP config  
3. Fill `PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN` (never commit the token)

| Host | Typical MCP config location |
|------|-----------------------------|
| Cursor | `~/.cursor/mcp.json` → `mcpServers` |
| Claude Code | `~/.claude.json` or project `.mcp.json` → `mcpServers` |
| Codex | `~/.codex/config.toml` → `[mcp_servers.…]` (stdio command/args/env) |
| OpenCode | `opencode.json` / config → MCP servers section |
| Pi | agent `settings.json` MCP / tools section |

If MCP is missing or the token is empty → **MarkItDown only** via `papers-knowledge-site`. Do not block the pipeline.

## Python scripts (in sibling skills)

Stage A CLIs live under `papers-library-pipeline/scripts/` (`papers_library_pipeline`).  
Stage B CLIs live under `papers-knowledge-site/scripts/` (`papers_knowledge_site`).  
The orchestrator does not ship harvest/convert packages; it only gates and routes.
