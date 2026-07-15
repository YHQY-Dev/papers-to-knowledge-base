"""Persist harvest/download source health (OpenAlex skip, Sci-Hub preferred)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_path: Path | None = None


def configure(path: Path | None) -> None:
    """Set process-global path for source-health.json (None = in-memory only)."""
    global _path
    _path = Path(path) if path is not None else None


def configured_path() -> Path | None:
    return _path


def reset_for_tests() -> None:
    """Clear configured path (tests)."""
    configure(None)


def utc_end_of_day(now: datetime | None = None) -> datetime:
    """Return 23:59:59+00:00 for the UTC calendar day of `now`."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)
    return now.replace(hour=23, minute=59, second=59, microsecond=0)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load(path: Path | None = None) -> dict[str, Any]:
    p = path if path is not None else _path
    if p is None or not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save(data: dict[str, Any], path: Path | None = None) -> None:
    p = path if path is not None else _path
    if p is None:
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(data)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(p)


def merge_save(updates: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    data = load(path)
    data.update(updates)
    save(data, path)
    return data


def openalex_skip_active(
    data: dict[str, Any] | None = None,
    *,
    now: datetime | None = None,
) -> str | None:
    """Return skip reason if OpenAlex should be skipped, else None."""
    data = data if data is not None else load()
    until = _parse_iso(data.get("openalex_skip_until"))
    if until is None:
        return None
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)
    if now < until:
        return str(data.get("openalex_skip_reason") or "openalex_skip_until active")
    return None


def mark_openalex_skip_for_utc_day(
    reason: str,
    *,
    now: datetime | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    """Persist skip until end of current UTC day. Does not shorten an existing later deadline."""
    now = now or datetime.now(timezone.utc)
    until = utc_end_of_day(now)
    data = load(path)
    existing = _parse_iso(data.get("openalex_skip_until"))
    if existing is not None and existing >= until:
        # Keep existing; still refresh reason if empty
        if not data.get("openalex_skip_reason"):
            return merge_save({"openalex_skip_reason": reason}, path)
        return data
    return merge_save(
        {
            "openalex_skip_until": until.isoformat(),
            "openalex_skip_reason": reason,
        },
        path,
    )


def clear_expired_openalex_skip(
    *,
    now: datetime | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    data = load(path)
    if openalex_skip_active(data, now=now) is not None:
        return data
    if "openalex_skip_until" not in data and "openalex_skip_reason" not in data:
        return data
    data.pop("openalex_skip_until", None)
    data.pop("openalex_skip_reason", None)
    save(data, path)
    return data


def get_scihub_preferred(path: Path | None = None) -> str | None:
    data = load(path)
    pref = data.get("scihub_preferred")
    return str(pref).rstrip("/") if pref else None


def set_scihub_preferred(url: str, path: Path | None = None) -> dict[str, Any]:
    url = url.rstrip("/")
    return merge_save(
        {
            "scihub_preferred": url,
            "scihub_last_ok_at": datetime.now(timezone.utc).isoformat(),
        },
        path,
    )
