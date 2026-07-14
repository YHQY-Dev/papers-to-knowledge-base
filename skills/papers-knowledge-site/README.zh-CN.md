# papers-knowledge-site

[English](README.md)

**Agent Skill（阶段 B）**：在已有录用 PDF（及 Excel/清单）的前提下，做 PDF→Markdown，并生成读者无需 npm 的静态 HTML 知识站。不负责批量搜论文或下载 PDF。

兼容 **Cursor**、**Claude Code**、**Codex**、**OpenCode**、**Pi**，以及遵循 [Agent Skills](https://agentskills.io)（`SKILL.md`）的其它宿主。

同属 `papers-to-knowledge-base` 技能族：

| Skill | 职责 |
|-------|------|
| `papers-to-knowledge-base` | 问诊 + 路由 |
| `papers-library-pipeline` | A：收获 → PDF → Excel |
| **`papers-knowledge-site`** | **B：PDF→MD → 静态站** |

## 你能得到什么

| 内容 | 作用 |
|------|------|
| `SKILL.md` | 转换与建站流程说明 |
| `scripts/papers_knowledge_site/` | MarkItDown 转换、插图抽取、引文线索 |
| `mcp/paddleocr.mcp.json.example` | **可选** PaddleOCR-VL MCP（扫描件） |
| `references/` | 静态站规范、OCR 说明、站点验收清单 |

**默认 PDF→Markdown：** [MarkItDown](https://github.com/microsoft/markitdown)。  
**可选 OCR：** PaddleOCR-VL MCP — 在 [AI Studio PaddleOCR](https://aistudio.baidu.com/paddleocr) 申请 token；未配置时继续用 MarkItDown。

**人读 PDF**；Markdown 主要供 AI 撰写站点内容。

## 前置条件

- `{DOMAIN}-pdf/` 下已有录用 PDF
- 录用名单（`{DOMAIN}-catalog/literature.xlsx` 和/或 manifest）
- `{LANG}` 与 OCR 偏好（编排器问诊结果；单独调用时需补问）

## 安装

只联接到**你正在用的那个 agent** 的 skills 目录。  
见仓库根 [README](../../README.zh-CN.md)，不要一次装到所有宿主。  
从零开始时建议同时联接编排 skill。

## 转换与建站（摘要）

```text
PDF + 录用名单 → 转换（有 PaddleOCR 则可用，否则 MarkItDown）
→ 术语表 → 章节 → 静态 HTML → 验收
```

```bash
# 在仓库根执行（与阶段 A 共用 uv workspace）
uv sync
uv run python -m papers_knowledge_site.pdf_to_md batch --pdf-dir {ROOT}/FIELD-pdf --md-dir {ROOT}/FIELD-md
```

对 agent 说：*「用 papers-knowledge-site 把这些 PDF 转成 Markdown 并建静态知识站」*。

站点规范：[references/static-html-site.md](references/static-html-site.md)。  
验收清单：[references/checklist.md](references/checklist.md)。

## 可选 PaddleOCR MCP

1. 在仓库根 `.env` 填写 `PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN=`（不要提交 `.env`）。  
2. 将 `mcp/paddleocr.mcp.json.example` 合并进各宿主 MCP（经 `uvx --env-file .env` 读 token）。  
3. 详见 [references/paddleocr-mcp.md](references/paddleocr-mcp.md)。

| 宿主 | 典型 MCP 配置位置 |
|------|-------------------|
| Cursor | `~/.cursor/mcp.json` → `mcpServers` |
| Claude Code | `~/.claude.json` 或项目 `.mcp.json` |
| Codex | `~/.codex/config.toml` → `[mcp_servers.…]` |
| OpenCode / Pi | 宿主 MCP / tools 设置 |

没有 token 时一律走 MarkItDown，不要卡住流水线。

## 目录结构

```text
papers-knowledge-site/
  SKILL.md
  README.md / README.zh-CN.md
  mcp/paddleocr.mcp.json.example
  references/
    static-html-site.md
    paddleocr-mcp.md
    checklist.md
  scripts/
    pyproject.toml
    papers_knowledge_site/   # Python 包
```

## 许可 / 说明

公开站点只引用 DOI/OA，不要链到本地 `*-pdf/` / `*-md/`。  
搜论文 / 下载 / Excel 请用 `papers-library-pipeline`。
