# `_dev/`

Pytest for Python packages under `skills/*/scripts/`. Not an installable skill.

## papers-library-pipeline

```powershell
cd skills/papers-library-pipeline/scripts
uv venv .venv --python 3.12
uv pip install -r requirements-dev.txt --python .venv
.\.venv\Scripts\python.exe -m pytest ../../../_dev/papers-library-pipeline -v
```
