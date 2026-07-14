# papers-to-knowledge-base

[中文说明](README.zh-CN.md)

Academic papers → local literature library and/or static HTML knowledge site.

| Skill | Role |
|-------|------|
| [`skills/papers-to-knowledge-base`](skills/papers-to-knowledge-base/) | Intake + routing |
| [`skills/papers-library-pipeline`](skills/papers-library-pipeline/) | **A** — harvest, triage, PDF, Excel |
| [`skills/papers-knowledge-site`](skills/papers-knowledge-site/) | **B** — PDF→Markdown, optional PaddleOCR, static site |

Each skill is a folder with `SKILL.md` (optional `scripts/`, `references/`, `mcp/`).

## Which skills to link

| Goal | Folders under `skills/` |
|------|-------------------------|
| Full pipeline | all three |
| Library only | orchestrator + `papers-library-pipeline` |
| Site only | orchestrator + `papers-knowledge-site` |

**Install only for the agent you use.** Paths differ by host — do not link into every skills directory at once.

Set `REPO` to your clone (folder that contains `skills/`), then pick a section below.

## Cursor

Personal: `~/.cursor/skills/<name>/`  
Project: `.cursor/skills/<name>/`

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

Personal: `~/.claude/skills/<name>/`  
Project: `.claude/skills/<name>/`

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.claude/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.claude/skills/$name
done
```

## Codex

Personal: `~/.agents/skills/<name>/`  
Project: `.agents/skills/<name>/`

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.agents/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.agents/skills/$name
done
```

## OpenCode

Personal: `~/.config/opencode/skills/<name>/`  
Project: `.opencode/skills/<name>/` (or `.agents/skills/` if your setup already uses it)

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.config/opencode/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.config/opencode/skills/$name
done
```

## Pi

Personal: `~/.pi/agent/skills/<name>/`  
Project: `.pi/skills/<name>/` (or `.agents/skills/` if your setup already uses it)

```bash
REPO=/path/to/papers-to-knowledge-base
mkdir -p ~/.pi/agent/skills
for name in papers-to-knowledge-base papers-library-pipeline papers-knowledge-site; do
  ln -sfn "$REPO/skills/$name" ~/.pi/agent/skills/$name
done
```

Reload / restart that agent after linking. More detail (MCP, project-scoped paths): [`skills/papers-to-knowledge-base/references/install-hosts.md`](skills/papers-to-knowledge-base/references/install-hosts.md).

## Python (shared tooling)

Separate from skill linking. One [uv](https://docs.astral.sh/uv/) workspace at the repo root:

```powershell
uv sync --group dev
uv run python -m papers_library_pipeline.run_harvest
uv run python -m papers_knowledge_site.pdf_to_md -h
uv run pytest _dev/papers-library-pipeline -v
```

Requires Python **3.12** or **3.13**.

## PDF naming (stage A)

`{local_id}.{sanitized_title}.pdf` — e.g. `1001.Guinier_approximation.pdf`.

## License

MIT — see [LICENSE](LICENSE).
