# `_dev/`

Pytest for workspace packages. Not an installable skill.

From repo root (after `uv sync --group dev`):

```powershell
# all tests (includes live OpenAlex / Crossref / PDF download)
uv run pytest _dev/papers-library-pipeline -v

# offline only
uv run pytest _dev/papers-library-pipeline -v -m "not network"
```

Optional: set `OPENALEX_API_KEY` in the repo-root `.env` (see `.env.example`) for higher OpenAlex quota on network tests. If the daily budget is exhausted, OpenAlex live tests **skip** (Crossref + PDF download still run).