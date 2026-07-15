# papers-library-pipeline

[English](README.md)

**Agent Skill（阶段 A）：** 收获、打分、下载并编目学术论文到本地文献库，并导出 Excel 精评表。不做 PDF→Markdown、不做 OCR、不建静态站。

属于 `papers-to-knowledge-base` 技能族。Intake/路由用编排 skill；Markdown/站点用 `papers-knowledge-site`。

兼容 **Cursor**、**Claude Code**、**Codex**、**OpenCode**、**Pi**，以及遵循 [Agent Skills](https://agentskills.io)（`SKILL.md`）的其它宿主。

## 你能得到什么

| 内容 | 作用 |
|------|------|
| `SKILL.md` | 仅文献库流程的 agent 规则 |
| `scripts/papers_library_pipeline/` | OpenAlex/Crossref 收获、PDF 下载（httpx）、PDF 清单同步、Excel 导出 |
| `references/checklist.md` | 文献库验收清单 |

**录用标记：** 优先写 `accepted`，`selected` 为别名；`--selected-only` 二者任一为真即可。  
**PDF 命名：** 仅 `{编号}.{标题}.pdf`（如 `1001.Guinier_approximation.pdf`）。  
**仅 A 目录：** 创建 `*-pdf/`、`*-candidates/`、`*-catalog/`，**不**创建 `*-md/` / `*-web/`。  
**源健康：** `{DOMAIN}-catalog/source-health.json` 记住 OpenAlex 当日跳过与上次可用的 Sci-Hub 镜像。  
**审阅门闸：** 进入精评前须问用户选 Full AI / 纯脚本 / 混合（见 `SKILL.md`）。  
**单元测试**不在本 skill 内：[`../../_dev/papers-library-pipeline/`](../../_dev/papers-library-pipeline/)。  
**并行 subagent**（宿主支持时）：[references/parallel-subagents.md](references/parallel-subagents.md)。

## 安装

只联接到**你正在用的那个 agent** 的 skills 目录（Cursor / Claude Code / Codex / …）。  
见仓库根 [README](../../README.zh-CN.md)，不要一次装到所有宿主。  
建议同时联接编排 skill，以便保留 intake 与路由。

## 脚本环境

仓库根目录的共用 uv workspace（与阶段 B 共用 `.venv`）：

```bash
# 在仓库根执行
uv sync
# 复制 scripts/domain_config.example.json → {ROOT}/domain_config.json
export DOMAIN_KB_CONFIG=/path/to/domain_config.json
uv run python -m papers_library_pipeline.run_harvest
uv run python -m papers_library_pipeline.pdf_fetch fetch-batch {ROOT}/FIELD-candidates/candidates.json \
  --pdf-dir {ROOT}/FIELD-pdf --manual {ROOT}/FIELD-catalog/manual-needed.md \
  --selected-only --assign-ids
uv run python -m papers_library_pipeline.sync_manifest
uv run python -m papers_library_pipeline.export_excel
```

Excel 输出路径：**`{DOMAIN}-catalog/literature.xlsx`**。

对 agent 说：*「用 papers-library-pipeline 为某某领域收获并下载论文」*。

## 目录结构

```text
papers-library-pipeline/
  SKILL.md
  README.md / README.zh-CN.md
  references/checklist.md
  scripts/
    pyproject.toml
    domain_config.example.json
    seed_works.example.json
    papers_library_pipeline/
```

## 边界

- **范围内：** 收获、精评、PDF 下载、编目、Excel
- **范围外：** MarkItDown、PaddleOCR、`{DOMAIN}-md/`、`{DOMAIN}-web/`
