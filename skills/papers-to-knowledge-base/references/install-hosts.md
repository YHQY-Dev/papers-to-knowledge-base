# Install by host

Default: install into the **current project** only. Do not use the personal/home skills directory unless the user asks for a global install.

## Which folders

| Folder under repo `skills/` | Role |
|-----------------------------|------|
| `papers-to-knowledge-base` | Orchestrator |
| `papers-library-pipeline` | Stage A |
| `papers-knowledge-site` | Stage B |

| Goal | Install these |
|------|---------------|
| Full | all three |
| Library only | orchestrator + A |
| Site only | orchestrator + B |

## Project paths (preferred)

Copy folders from this repo’s `skills/` into:

| Host | Under the project |
|------|-------------------|
| Cursor | `.cursor/skills/<name>/` |
| Claude Code | `.claude/skills/<name>/` |
| Codex | `.agents/skills/<name>/` |
| OpenCode | `.opencode/skills/<name>/` |
| Pi | `.pi/skills/<name>/` |

Each installed folder must contain `SKILL.md`. Prefer **copy**. Reload the agent afterward.

**Agent anti-patterns**

- Do not `git clone` a second full copy into temp just to move files, if this repo is already the workspace  
- Do not write to `~/.cursor/skills` (etc.) unless the user wants personal/global skills  

## Personal paths (optional)

| Host | Personal path |
|------|---------------|
| Cursor | `~/.cursor/skills/<name>/` |
| Claude Code | `~/.claude/skills/<name>/` |
| Codex | `~/.agents/skills/<name>/` |
| OpenCode | `~/.config/opencode/skills/<name>/` |
| Pi | `~/.pi/agent/skills/<name>/` |

## How discovery works

| Host | Notes |
|------|-------|
| Cursor | Project `.cursor/skills` and/or personal `~/.cursor/skills` |
| Claude Code | Project `.claude/skills` and/or `~/.claude/skills` |
| Codex | Project `.agents/skills` and/or `~/.agents/skills` |
| OpenCode | Native skill tool; loads on demand |
| Pi | Lists skills; may use `/skill:<name>` |

## Optional PaddleOCR MCP (stage B)

1. Token: https://aistudio.baidu.com/paddleocr  
2. Merge `mcp/paddleocr.mcp.json.example` into **that host’s** MCP config  
3. Set `PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN` (never commit)

| Host | Typical MCP config |
|------|--------------------|
| Cursor | `~/.cursor/mcp.json` → `mcpServers` |
| Claude Code | `~/.claude.json` or project `.mcp.json` |
| Codex | `~/.codex/config.toml` → `[mcp_servers.…]` |
| OpenCode | `opencode.json` MCP section |
| Pi | agent settings MCP / tools |

Missing token → MarkItDown only via `papers-knowledge-site`.

## Python

`uv sync` at **this repo’s root** (shared by A and B). Separate from where you put skills for discovery.
