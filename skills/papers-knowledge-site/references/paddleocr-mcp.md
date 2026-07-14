# Optional: PaddleOCR-VL MCP（扫描件 / 版面 OCR）

**Skill:** `papers-knowledge-site` (stage B only).  
**Default path is still MarkItDown** (`pdf_to_md`). Use this MCP only when the user configured a token and text-layer PDF conversion is insufficient (scanned pages, image-heavy papers).

This skill does **not** harvest or download papers. OCR/convert applies to accepted PDFs already under `{DOMAIN}-pdf/`.

## 1. Get a token → put it in repo `.env`

1. Open [Baidu AI Studio PaddleOCR](https://aistudio.baidu.com/paddleocr)
2. Apply / create an access token
3. In the **repo root**, copy `.env.example` → `.env` (if needed) and set:

```env
PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN=your_token_here
```

Do **not** commit `.env`. OpenAlex can share the same file (`OPENALEX_API_KEY=`).

## 2. Wire into the host MCP config

Template: `mcp/paddleocr.mcp.json.example`. Token stays in `.env`; MCP loads it via `uvx --env-file`.

```json
"PaddleOCR-VL-1.6": {
  "command": "uvx",
  "args": [
    "--env-file", ".env",
    "--from", "paddleocr-mcp",
    "paddleocr_mcp"
  ],
  "env": {
    "PADDLEOCR_MCP_MODEL": "PaddleOCR-VL-1.6",
    "PADDLEOCR_MCP_PPOCR_SOURCE": "aistudio"
  }
}
```

If the MCP process cwd is **not** the repo root (common for a global `~/.cursor/mcp.json`), change `.env` to an **absolute** path, e.g. `D:/path/to/papers-to-knowledge-base/.env`.

| Host | Where to merge |
|------|----------------|
| Cursor | project `.cursor/mcp.json` (preferred) or `~/.cursor/mcp.json` |
| Claude Code | `~/.claude.json` or project `.mcp.json` |
| Codex | `~/.codex/config.toml` `[mcp_servers.…]` (same command/args/env) |
| OpenCode / Pi | Host MCP / tools settings (stdio + env) |

Requires local `uv` / `uvx`. Reload MCP after edit. Server id may appear as `PaddleOCR-VL-1.6` or `user-PaddleOCR-VL-1.6`.

Omit the server or leave the `.env` token empty → agents **must** use MarkItDown only.

## 3. Agent usage

1. `GetMcpTools` on `user-PaddleOCR-VL-1.6` (or `mcp_auth` if `needsAuth`).
2. If server missing / auth fails / tool errors → **fall back** to  
   `python -m papers_knowledge_site.pdf_to_md convert …`
3. Call `paddleocr_vl`:

| Arg | Notes |
|-----|--------|
| `input_data` | **Absolute** PDF path (no relative paths) |
| `file_type` | `"pdf"` |
| `output_mode` | `"simple"` (plain text/markdown-ish) or `"detailed"` |
| `return_images` | `true` preferred when figures matter |

4. Persist with the same folder contract as MarkItDown:

```python
from papers_knowledge_site.pdf_to_md import write_md_bundle

write_md_bundle(
    pdf_path,
    out_dir,           # {DOMAIN}-md/{id}
    ocr_text,
    converter="paddleocr-vl",
    extract_images=True,
)
```

Prefer `write_md_bundle` in-process; no need for a temp-file CLI after OCR.

## 4. Decision rule

```text
if PaddleOCR MCP ready AND (user asked for OCR OR MarkItDown output nearly empty / scanned PDF):
    paddleocr_vl → write_md_bundle
else:
    pdf_to_md (MarkItDown)
```

Never block the site pipeline on a missing token.
