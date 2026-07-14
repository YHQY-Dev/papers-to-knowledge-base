# papers-to-knowledge-base

[English](README.md)

学术论文 → 本地文献库，和/或静态 HTML 知识站。

| Skill | 作用 |
|-------|------|
| [`skills/papers-to-knowledge-base`](skills/papers-to-knowledge-base/) | Intake + 路由 |
| [`skills/papers-library-pipeline`](skills/papers-library-pipeline/) | **A** — 收获、精评、PDF、Excel |
| [`skills/papers-knowledge-site`](skills/papers-knowledge-site/) | **B** — PDF→Markdown、可选 PaddleOCR、静态站 |

每个 skill 是含 `SKILL.md` 的目录（可选 `scripts/`、`references/`、`mcp/`）。适用于 Cursor、Claude Code、Codex、OpenCode、Pi 等支持 [Agent Skills](https://agentskills.io) 的宿主。

## 安装

| 目标 | 安装 `skills/` 下这些目录 |
|------|---------------------------|
| 全流程 | 三个全部 |
| 仅文献库 | 编排 + `papers-library-pipeline` |
| 仅建站 | 编排 + `papers-knowledge-site` |

**Windows（PowerShell）：**

```powershell
$root = "D:\software\SAS\Skill\skills"   # 或你的 clone 路径\skills
$hosts = @(
  "$env:USERPROFILE\.agents\skills",
  "$env:USERPROFILE\.claude\skills",
  "$env:USERPROFILE\.cursor\skills",
  "$env:USERPROFILE\.pi\agent\skills",
  "$env:USERPROFILE\.config\opencode\skills"
)
foreach ($name in @(
  "papers-to-knowledge-base",
  "papers-library-pipeline",
  "papers-knowledge-site"
)) {
  $src = Join-Path $root $name
  foreach ($h in $hosts) {
    New-Item -ItemType Directory -Force -Path $h | Out-Null
    New-Item -ItemType Junction -Force -Path (Join-Path $h $name) -Target $src | Out-Null
  }
}
```

**Unix / macOS：**

```bash
SRC=/absolute/path/to/repo/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  mkdir -p ~/.agents/skills ~/.claude/skills ~/.cursor/skills \
           ~/.pi/agent/skills ~/.config/opencode/skills
  ln -sfn "$SRC/$name" ~/.agents/skills/$name
  ln -sfn "$SRC/$name" ~/.claude/skills/$name
  ln -sfn "$SRC/$name" ~/.cursor/skills/$name
  ln -sfn "$SRC/$name" ~/.pi/agent/skills/$name
  ln -sfn "$SRC/$name" ~/.config/opencode/skills/$name
done
```

完成后重载 agent。更多说明：[`skills/papers-to-knowledge-base/references/install-hosts.md`](skills/papers-to-knowledge-base/references/install-hosts.md)。

## `_dev/`

`skills/*/scripts/` 下 Python 包的 pytest。不会作为 skill 安装。

```powershell
cd skills\papers-library-pipeline\scripts
uv venv .venv --python 3.12
uv pip install -r requirements-dev.txt --python .venv
.\.venv\Scripts\python.exe -m pytest ..\..\..\_dev\papers-library-pipeline -v
```

## PDF 命名（阶段 A）

`{编号}.{标题}.pdf`，例如 `1001.Guinier_approximation.pdf`。

## 许可

MIT — 见 [LICENSE](LICENSE)。
