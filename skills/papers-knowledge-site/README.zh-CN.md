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

## 快速安装

推荐用 **符号链接 / 目录联接**，一份源码给所有工具用。

```bash
mkdir -p ~/.agents/skills
ln -s /absolute/path/to/papers-knowledge-site ~/.agents/skills/papers-knowledge-site

mkdir -p ~/.claude/skills
ln -s /absolute/path/to/papers-knowledge-site ~/.claude/skills/papers-knowledge-site

mkdir -p ~/.cursor/skills
ln -s /absolute/path/to/papers-knowledge-site ~/.cursor/skills/papers-knowledge-site
```

**Windows PowerShell：**

```powershell
$src = "D:\software\SAS\Skill\skills\papers-knowledge-site"
New-Item -ItemType Junction -Force -Path "$env:USERPROFILE\.agents\skills\papers-knowledge-site" -Target $src
New-Item -ItemType Junction -Force -Path "$env:USERPROFILE\.claude\skills\papers-knowledge-site" -Target $src
New-Item -ItemType Junction -Force -Path "$env:USERPROFILE\.cursor\skills\papers-knowledge-site" -Target $src
```

另可联接到 `~/.config/opencode/skills/`、`~/.pi/agent/skills/`，或项目内 `.agents/skills/`。

安装后请重启 / 重载 agent。

## 转换与建站（摘要）

```text
PDF + 录用名单 → 转换（有 PaddleOCR 则可用，否则 MarkItDown）
→ 术语表 → 章节 → 静态 HTML → 验收
```

```bash
cd scripts
pip install -r requirements.txt
python -m papers_knowledge_site.pdf_to_md batch --pdf-dir ../FIELD-pdf --md-dir ../FIELD-md
```

对 agent 说：*「用 papers-knowledge-site 把这些 PDF 转成 Markdown 并建静态知识站」*。

站点规范：[references/static-html-site.md](references/static-html-site.md)。  
验收清单：[references/checklist.md](references/checklist.md)。

## 可选 PaddleOCR MCP

1. 将 `mcp/paddleocr.mcp.json.example` 合并进各宿主的 MCP 配置。  
2. 填写 `PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN`（不要提交进 git）。  
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
    requirements.txt
    papers_knowledge_site/   # Python 包
```

## 许可 / 说明

脚本可复制到项目 `{ROOT}/scripts/`，或通过 `PYTHONPATH` 调用。  
公开站点只引用 DOI/OA，不要链到本地 `*-pdf/` / `*-md/`。  
搜论文 / 下载 / Excel 请用 `papers-library-pipeline`。
