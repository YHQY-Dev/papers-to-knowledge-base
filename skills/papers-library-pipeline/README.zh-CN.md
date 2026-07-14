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
**单元测试**不在本 skill 内：[`../../_dev/papers-library-pipeline/`](../../_dev/papers-library-pipeline/)。

## 快速安装

```bash
mkdir -p ~/.agents/skills
ln -s /absolute/path/to/papers-library-pipeline ~/.agents/skills/papers-library-pipeline
```

**Windows PowerShell：**

```powershell
$src = "D:\software\SAS\Skill\skills\papers-library-pipeline"
New-Item -ItemType Junction -Force -Path "$env:USERPROFILE\.agents\skills\papers-library-pipeline" -Target $src
New-Item -ItemType Junction -Force -Path "$env:USERPROFILE\.cursor\skills\papers-library-pipeline" -Target $src
```

建议与编排 skill 一起安装，以便保留 intake 与路由。

## 脚本环境

```bash
cd scripts
pip install -r requirements.txt
# 复制 domain_config.example.json → {ROOT}/domain_config.json
export DOMAIN_KB_CONFIG=/path/to/domain_config.json
python -m papers_library_pipeline.run_harvest
python -m papers_library_pipeline.pdf_fetch fetch-batch ../FIELD-candidates/candidates.json \
  --pdf-dir ../FIELD-pdf --manual ../FIELD-catalog/manual-needed.md \
  --selected-only --assign-ids
python -m papers_library_pipeline.sync_manifest
python -m papers_library_pipeline.export_excel
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
    requirements.txt
    domain_config.example.json
    seed_works.example.json
    papers_library_pipeline/
    tests/
```

## 边界

- **范围内：** 收获、精评、PDF 下载、编目、Excel
- **范围外：** MarkItDown、PaddleOCR、`{DOMAIN}-md/`、`{DOMAIN}-web/`
