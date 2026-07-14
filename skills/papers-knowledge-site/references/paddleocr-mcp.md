# Optional: PaddleOCR-VL MCP（扫描件 / 版面 OCR）

**Skill:** `papers-knowledge-site` (stage B only).  
**Default path is still MarkItDown** (`pdf_to_md`). Use this MCP only when the user configured a token and text-layer PDF conversion is insufficient (scanned pages, image-heavy papers).

This skill does **not** harvest or download papers. OCR/convert applies to accepted PDFs already under `{DOMAIN}-pdf/`.

## 1. Get a token

1. Open [Baidu AI Studio PaddleOCR](https://aistudio.baidu.com/paddleocr)
2. Apply / create an access token
3. Put it in **your host’s** MCP config (do **not** commit the token into git)

## 2. Wire into the host MCP config

Template: `mcp/paddleocr.mcp.json.example` (JSON `mcpServers` shape used by Cursor / Claude Code / many hosts).

```json
"PaddleOCR-VL-1.6": {
  "command": "uvx",
  "args": ["--from", "paddleocr-mcp", "paddleocr_mcp"],
  "env": {
    "PADDLEOCR_MCP_MODEL": "PaddleOCR-VL-1.6",
    "PADDLEOCR_MCP_PPOCR_SOURCE": "aistudio",
    "PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN": "<YOUR_TOKEN>"
  }
}
```

| Host | Where to merge |
|------|----------------|
| Cursor | `~/.cursor/mcp.json` |
| Claude Code | `~/.claude.json` or project `.mcp.json` |
| Codex | `~/.codex/config.toml` `[mcp_servers.…]` (same command/args/env) |
| OpenCode / Pi | Host MCP / tools settings (stdio + env) |

Requires local `uv` / `uvx`. Reload MCP after edit. Server id may appear as `PaddleOCR-VL-1.6` or `user-PaddleOCR-VL-1.6`.

Leave `ACCESS_TOKEN` empty or omit the server → agents **must** use MarkItDown only.

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
