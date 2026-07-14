# papers-to-knowledge-base

[English](README.md)

学术论文 → 本地文献库，和/或静态 HTML 知识站。

| Skill | 作用 |
|-------|------|
| [`skills/papers-to-knowledge-base`](skills/papers-to-knowledge-base/) | Intake + 路由 |
| [`skills/papers-library-pipeline`](skills/papers-library-pipeline/) | **A** — 收获、精评、PDF、Excel |
| [`skills/papers-knowledge-site`](skills/papers-knowledge-site/) | **B** — PDF→Markdown、可选 PaddleOCR、静态站 |

每个 skill 是含 `SKILL.md` 的目录（可选 `scripts/`、`references/`、`mcp/`）。

## 要联接哪些 skill

| 目标 | 安装 `skills/` 下这些目录 |
|------|---------------------------|
| 全流程 | 三个全部 |
| 仅文献库 | 编排 + `papers-library-pipeline` |
| 仅建站 | 编排 + `papers-knowledge-site` |

**只安装你正在用的那个 agent 对应的目录**，不要一次链到所有宿主。

把 `REPO` 设成你的克隆路径（含 `skills/` 的那一层），再选下面一节。

## Cursor

个人：`~/.cursor/skills/<name>/`  
项目：`.cursor/skills/<name>/`

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

## Claude Code

个人：`~/.claude/skills/<name>/`  
项目：`.claude/skills/<name>/`

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.claude/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.claude/skills/$name
done
```

## Codex

个人：`~/.agents/skills/<name>/`  
项目：`.agents/skills/<name>/`

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.agents/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.agents/skills/$name
done
```

## OpenCode

个人：`~/.config/opencode/skills/<name>/`  
项目：`.opencode/skills/<name>/`（若你已用 `.agents/skills/` 也可）

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.config/opencode/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.config/opencode/skills/$name
done
```

## Pi

个人：`~/.pi/agent/skills/<name>/`  
项目：`.pi/skills/<name>/`（若你已用 `.agents/skills/` 也可）

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.pi/agent/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.pi/agent/skills/$name
done
```

联接后请重载 / 重启**该** agent。更多说明（MCP、项目级路径）：[`skills/papers-to-knowledge-base/references/install-hosts.md`](skills/papers-to-knowledge-base/references/install-hosts.md)。

## Python（共用工具）

与 skill 联接无关。仓库根用 [uv](https://docs.astral.sh/uv/) workspace：

```powershell
uv sync --group dev
uv run python -m papers_library_pipeline.run_harvest
uv run python -m papers_knowledge_site.pdf_to_md -h
uv run pytest _dev/papers-library-pipeline -v
```

需要 Python **3.12** 或 **3.13**。

## PDF 命名（阶段 A）

`{编号}.{标题}.pdf`，例如 `1001.Guinier_approximation.pdf`。

## 许可

MIT — 见 [LICENSE](LICENSE)。
