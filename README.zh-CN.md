# papers-to-knowledge-base

[English](README.md)

把某一领域的学术论文，收成**本地文献库**，并按需做成**可浏览的静态知识站**。

面向用 Cursor / Claude Code / Codex 等 AI 编程助手的人：装上本仓库的 Agent Skills 后，对助手说清领域与目标，它会按流程搜文献、下载 PDF、导出 Excel，再（可选）转成 Markdown 并生成静态 HTML 教程站。

## 要解决什么问题

做专题调研时，常见卡点是：

- 论文散落在 OpenAlex / Crossref / 各出版商，难统一下载与编号  
- 录用 / 淘汰靠脑记，缺少可打开的 Excel 清单  
- 人要读 PDF，AI 建站又需要 Markdown；扫描件还可能要 OCR  
- 希望最后有一个**离线可打开**的知识/教程站，而不是一堆聊天记录  

本仓库把这件事拆成可复用的技能与脚本，而不是一次性手工流水线。

## 能做什么

| 能力 | 说明 |
|------|------|
| 问诊后开跑 | 先确认：只要文献库、只要建站，还是「库 → 站」全流程；确认前不批量下载 / 转换 |
| 文献收获 | OpenAlex + Crossref 按主题搜、去重、粗打分；宿主支持 subagent 时可按主题分片并行搜 |
| 精评与录用 | AI/人工精评；`accepted` 标记；理由写进清单；可多 subagent 并行打分后由主会话合并 |
| PDF 下载 | 按 DOI 尝试获取；失败记入 `manual-needed.md` |
| Excel 目录 | `{领域}-catalog/literature.xlsx`（编号、题名、DOI、分数、是否录用、PDF 状态等） |
| PDF→Markdown | 默认 MarkItDown；扫描件可选用 PaddleOCR MCP |
| 静态知识站 | 术语表 + 章节 + 纯 HTML（无需 `npm install` 才能阅读） |

**不做的事：** 不替你写完所有科研结论；不把本地 PDF 路径公开上网；不替代你对录用名单的最终确认。

## 三种用法

| 用法 | 适合 | 结果 |
|------|------|------|
| **仅文献库（A）** | 只要 PDF + Excel，自己读论文 | `{领域}-pdf/`、`literature.xlsx` 等 |
| **仅建站（B）** | 已有录用 PDF（和清单） | `{领域}-md/` + `{领域}-web/` 静态站 |
| **全流程（A→B）** | 从搜文献做到站点 | 先 A，你确认 Excel 后再 B |

对助手可以说例如：

- *「用 papers-to-knowledge-base，给我做固态电解质文献库，先只要 PDF 和 Excel。」*  
- *「PDF 已经齐了，用 papers-knowledge-site 做成中文知识站。」*

## 仓库里有什么

三个可安装的 Agent Skill（装到**你正在用的那个**助手的 skills 目录即可）：

| 目录 | 职责 |
|------|------|
| [`skills/papers-to-knowledge-base`](skills/papers-to-knowledge-base/) | 编排：问诊、变量绑定、路由到 A / B |
| [`skills/papers-library-pipeline`](skills/papers-library-pipeline/) | A：收获 → 精评 → 下载 → Excel |
| [`skills/papers-knowledge-site`](skills/papers-knowledge-site/) | B：PDF→MD → 站点 |

脚本用仓库根的 **uv** 共用环境（与装哪个助手无关）：

```powershell
uv sync --group dev
uv run python -m papers_library_pipeline.run_harvest
uv run python -m papers_knowledge_site.pdf_to_md -h
```

需要 Python **3.12** 或 **3.13**。PDF 文件名：`{编号}.{标题}.pdf`。

### 密钥（`.env`）

在仓库根复制并编辑（**不要提交** `.env`）：

```powershell
Copy-Item .env.example .env
# 编辑 .env：
#   OPENALEX_API_KEY=...                 # https://openalex.org/settings/api
#   PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN=...  # https://aistudio.baidu.com/paddleocr
```

收获脚本会自动读取 `.env`。PaddleOCR MCP 模板用 `uvx --env-file .env`，无需把 token 写进 `mcp.json`。

## 安装 skill（按助手）

| 目标 | 联接 `skills/` 下这些目录 |
|------|---------------------------|
| 全流程 | 三个全部 |
| 仅文献库 | 编排 + `papers-library-pipeline` |
| 仅建站 | 编排 + `papers-knowledge-site` |

**只安装你正在用的那个助手**，不要一次链到所有宿主。把 `REPO` 设成克隆根目录（含 `skills/`），再选下面一节。

### Cursor

个人：`~/.cursor/skills/<name>/` · 项目：`.cursor/skills/<name>/`

```powershell
$REPO = "D:\path\to\papers-to-knowledge-base"
$dest = "$env:USERPROFILE\.cursor\skills"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
foreach ($name in @(
  "papers-to-knowledge-base",
  "papers-library-pipeline",
  "papers-knowledge-site"
)) {
  New-Item -ItemType Junction -Force -Path "$dest\$name" -Target "$REPO\skills\$name" | Out-Null
}
```

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.cursor/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.cursor/skills/$name
done
```

### Claude Code

个人：`~/.claude/skills/<name>/` · 项目：`.claude/skills/<name>/`

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.claude/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.claude/skills/$name
done
```

### Codex

个人：`~/.agents/skills/<name>/` · 项目：`.agents/skills/<name>/`

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.agents/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.agents/skills/$name
done
```

### OpenCode

个人：`~/.config/opencode/skills/<name>/` · 项目：`.opencode/skills/<name>/`

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.config/opencode/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.config/opencode/skills/$name
done
```

### Pi

个人：`~/.pi/agent/skills/<name>/` · 项目：`.pi/skills/<name>/`

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.pi/agent/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.pi/agent/skills/$name
done
```

联接后重载该助手。MCP、项目级路径等见 [`skills/papers-to-knowledge-base/references/install-hosts.md`](skills/papers-to-knowledge-base/references/install-hosts.md)。

## 许可

MIT — 见 [LICENSE](LICENSE)。
