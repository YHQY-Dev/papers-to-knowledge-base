# Install by host

Install **only for the agent you use**. Each host scans a different skills directory.

## Which folders

| Folder under repo `skills/` | Role |
|-----------------------------|------|
| `papers-to-knowledge-base` | Orchestrator |
| `papers-library-pipeline` | Stage A |
| `papers-knowledge-site` | Stage B |

| Goal | Link these |
|------|------------|
| Full | all three |
| Library only | orchestrator + A |
| Site only | orchestrator + B |

Commands for each host are in the [repo README](../../../README.md). Summary of destinations:

| Host | Personal path | Project path |
|------|---------------|--------------|
| Cursor | `~/.cursor/skills/<name>/` | `.cursor/skills/<name>/` |
| Claude Code | `~/.claude/skills/<name>/` | `.claude/skills/<name>/` |
| Codex | `~/.agents/skills/<name>/` | `.agents/skills/<name>/` |
| OpenCode | `~/.config/opencode/skills/<name>/` | `.opencode/skills/<name>/` |
| Pi | `~/.pi/agent/skills/<name>/` | `.pi/skills/<name>/` |

Reload that agent after linking.

## How discovery works

| Host | Notes |
|------|-------|
| Cursor | Reads `~/.cursor/skills` / project `.cursor/skills` |
| Claude Code | Reads `~/.claude/skills` / `.claude/skills` |
| Codex | Reads `~/.agents/skills` / `.agents/skills` |
| OpenCode | Native skill tool; loads on demand |
| Pi | Lists skills; may use `/skill:<name>` |

Tool names in `SKILL.md` are host-agnostic intent (shell / edit / read / MCP). Map them to the host’s tools.

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

`uv sync` at the **repo root** (shared by A and B). Not related to which agent skills directory you linked.
