"""Load repo-root `.env` into process env (OPENALEX_API_KEY, etc.)."""

from __future__ import annotations

from pathlib import Path

_LOADED = False


def load_repo_env(*, override: bool = False) -> Path | None:
    """Find and load the nearest `.env` (repo root preferred). Idempotent."""
    global _LOADED
    if _LOADED and not override:
        return None
    try:
        from dotenv import load_dotenv
    except ImportError:
        return None

    starts = [Path.cwd().resolve(), Path(__file__).resolve().parent]
    seen: set[Path] = set()
    for start in starts:
        for folder in [start, *start.parents]:
            if folder in seen:
                continue
            seen.add(folder)
            env_path = folder / ".env"
            if env_path.is_file():
                load_dotenv(env_path, override=override)
                _LOADED = True
                return env_path
    # Fallback: dotenv default search from cwd
    load_dotenv(override=override)
    _LOADED = True
    return None
