# papers-to-knowledge-base

[English](README.md)

面向学术论文的 **编排 Agent Skill**：负责两阶段 intake，并路由到文献库流水线（A）和/或静态知识站（B）。

兼容 **Cursor**、**Claude Code**、**Codex**、**OpenCode**、**Pi**，以及遵循 [Agent Skills](https://agentskills.io)（`SKILL.md` 目录结构）的其它宿主。

## Skill 家族

| Skill 目录 | 作用 |
|------------|------|
| `papers-to-knowledge-base` | Intake（Q0 + Phase 1/2）与路由 |
| `papers-library-pipeline` | **A** — 收获、精评、PDF 下载、Excel 目录 |
| `papers-knowledge-site` | **B** — PDF→Markdown、可选 PaddleOCR、静态 HTML 站 |

## Q0 / Phase 1 行为（摘要）

- **Q0：** 仅文献库（A）/ 仅建站（B）/ 全流程（A→B）  
- **Phase 1 Q1–Q3** 始终询问（领域、`{N}`、`{ROOT}`）——**仅建站**若沿用已有 PDF/Excel，可跳过 `{N}`  
- **Q4 `{LANG}` + Q5 PaddleOCR** 仅在 **B** 或 **A→B** 时询问  
- **仅文献库路径跳过语言与 OCR 问题**  
- 用户确认 intake 摘要之前，禁止收获 / 下载 / 转换 / 建站  

完整话术见 [references/intake.md](references/intake.md)。

## 安装矩阵

| 目标 | 需安装的 skill |
|------|----------------|
| 全流程 | 三个目录全部安装 |
| 仅文献库 | 本编排 skill + `papers-library-pipeline` |
| 仅建站 | 本编排 skill + `papers-knowledge-site` |

多宿主路径：[references/install-hosts.md](references/install-hosts.md)。安装命令也见仓库根 [README](../../README.zh-CN.md)。

## 可选 PaddleOCR MCP（阶段 B）

在仓库根 `.env` 填写 `PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN=`，再将 [`mcp/paddleocr.mcp.json.example`](mcp/paddleocr.mcp.json.example) 合并进宿主 MCP（通过 `--env-file .env` 读取）。无 token 时 B 仅用 MarkItDown。

## 目录结构

```text
papers-to-knowledge-base/
  SKILL.md
  README.md / README.zh-CN.md
  mcp/paddleocr.mcp.json.example
  references/
    intake.md
    install-hosts.md
```

## 许可

MIT。脚本与阶段逻辑在兄弟 skill 目录中。
