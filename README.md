# papers-to-knowledge-base

[中文说明](README.zh-CN.md)

Academic papers → local literature library and/or static HTML knowledge site.

| Skill | Role |
|-------|------|
| [`skills/papers-to-knowledge-base`](skills/papers-to-knowledge-base/) | Intake + routing |
| [`skills/papers-library-pipeline`](skills/papers-library-pipeline/) | **A** — harvest, triage, PDF, Excel |
| [`skills/papers-knowledge-site`](skills/papers-knowledge-site/) | **B** — PDF→Markdown, optional PaddleOCR, static site |

Each skill is a folder with `SKILL.md` (optional `scripts/`, `references/`, `mcp/`). Works with Cursor, Claude Code, Codex, OpenCode, Pi, and other [Agent Skills](https://agentskills.io) hosts.

## Install

| Goal | Folders under `skills/` |
|------|-------------------------|
| Full pipeline | all three |
| Library only | orchestrator + `papers-library-pipeline` |
| Site only | orchestrator + `papers-knowledge-site` |

**Windows (PowerShell):**

```powershell
$root = "D:\software\SAS\Skill\skills"   # or your clone path\skills
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

**Unix / macOS:**

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

Reload the agent afterward. More detail: [`skills/papers-to-knowledge-base/references/install-hosts.md`](skills/papers-to-knowledge-base/references/install-hosts.md).

## `_dev/`

Pytest for Python packages under `skills/*/scripts/`. Not installed as a skill.

```powershell
cd skills\papers-library-pipeline\scripts
uv venv .venv --python 3.12
uv pip install -r requirements-dev.txt --python .venv
.\.venv\Scripts\python.exe -m pytest ..\..\..\_dev\papers-library-pipeline -v
```

## PDF naming (stage A)

`{local_id}.{sanitized_title}.pdf` — e.g. `1001.Guinier_approximation.pdf`.

## License

MIT — see [LICENSE](LICENSE).
