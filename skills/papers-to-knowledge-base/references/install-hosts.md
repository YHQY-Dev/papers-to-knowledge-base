# Install by host

## Agent rule (default)

Install **only** the folders under this repo’s `skills/` **directly into the current project’s** skills directory.

- Source: `https://github.com/YHQY-Dev/papers-to-knowledge-base` → `skills/<name>/`
- Target: project `.cursor/skills/<name>/` (or host row below)
- Do **not** treat a full-repo clone as the install result
- Do **not** install to `~/…/skills` unless the user asks for personal/global

## Which folders

| Folder under `skills/` | Role |
|------------------------|------|
| `papers-to-knowledge-base` | Orchestrator |
| `papers-library-pipeline` | Stage A |
| `papers-knowledge-site` | Stage B |

| Goal | Folders |
|------|---------|
| Full | all three |
| Library only | orchestrator + A |
| Site only | orchestrator + B |

## Project install targets

| Host | Directory under the project |
|------|-----------------------------|
| Cursor | `.cursor/skills/` |
| Claude Code | `.claude/skills/` |
| Codex | `.agents/skills/` |
| OpenCode | `.opencode/skills/` |
| Pi | `.pi/skills/` |

Each installed `<name>/` must contain `SKILL.md` and the rest of that skill tree. Reload the agent afterward.

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

`uv sync` at **this repo’s root** (shared by A and B) when you need to run harvest / PDF→MD scripts. Separate from skill discovery paths.
