from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def norm_title(title: str | None) -> str:
    return re.sub(r"\W+", " ", (title or "").lower()).strip()


def _truthy_flag(value: Any) -> bool | None:
    """Return True/False for known flags, None if unset/unknown."""
    if value is None or value == "":
        return None
    if value is True or value is False:
        return value
    if value in (1, 0):
        return bool(value)
    if isinstance(value, str):
        s = value.strip()
        low = s.lower()
        if low in {"yes", "y", "true", "1"} or s == "是":
            return True
        if low in {"no", "n", "false", "0"} or s == "否":
            return False
    return None


def is_accepted(rec: dict[str, Any]) -> bool:
    """True if record is marked for download/handoff via `accepted` or `selected`."""
    return any(_truthy_flag(rec.get(f)) is True for f in ("accepted", "selected"))


def record_key(rec: dict[str, Any]) -> str:
    doi = (rec.get("doi") or "").lower().strip()
    if doi:
        return f"doi:{doi}"
    isbn = (rec.get("isbn") or "").replace("-", "").strip()
    if isbn:
        return f"isbn:{isbn}"
    return f"title:{norm_title(rec.get('title'))}"


def load_candidates_doc(path: Path, next_id_start: int = 1000) -> dict[str, Any]:
    if not path.exists():
        return {"next_id": next_id_start, "count": 0, "items": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"next_id": next_id_start, "count": len(data), "items": data}
    items = data.get("items") or []
    return {
        "next_id": int(data.get("next_id") or next_id_start),
        "count": len(items),
        "items": items,
    }


def load_candidates(path: Path) -> list[dict[str, Any]]:
    return load_candidates_doc(path)["items"]


def save_candidates(
    path: Path,
    items: list[dict[str, Any]],
    next_id: int | None = None,
) -> None:
    """Write candidates.json atomically (temp file + replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"count": len(items), "items": items}
    if next_id is not None:
        payload["next_id"] = int(next_id)
    elif path.exists():
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(old, dict) and old.get("next_id") is not None:
                payload["next_id"] = int(old["next_id"])
        except Exception:
            pass
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def merge_and_save(
    path: Path,
    existing: list[dict[str, Any]],
    new_items: list[dict[str, Any]],
    *,
    next_id: int | None = None,
) -> list[dict[str, Any]]:
    """Merge new records into existing, persist immediately, return merged list."""
    if not new_items:
        return existing
    merged = merge_records(existing, new_items)
    save_candidates(path, merged, next_id=next_id)
    return merged


def checkpoint_merge(
    path: Path,
    new_items: list[dict[str, Any]],
    *,
    next_id: int | None = None,
    next_id_start: int = 1000,
) -> list[dict[str, Any]]:
    """Reload candidates from disk, merge `new_items`, save."""
    if not new_items:
        doc = load_candidates_doc(path, next_id_start=next_id_start)
        return doc["items"]
    doc = load_candidates_doc(path, next_id_start=next_id_start)
    items = doc["items"]
    nid = next_id if next_id is not None else int(doc.get("next_id") or next_id_start)
    return merge_and_save(path, items, new_items, next_id=nid)


def theme_slug(theme: str) -> str:
    """Filesystem-safe id for a harvest theme (stable hash suffix)."""
    raw = (theme or "").strip()
    base = re.sub(r"[^\w\-]+", "_", raw.lower(), flags=re.UNICODE).strip("_")
    base = (base[:60] or "theme")
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    return f"{base}.{digest}"


def shards_dir_for(candidates_path: Path) -> Path:
    return Path(candidates_path).parent / "shards"


def shard_path(shards_dir: Path, theme: str, api: str) -> Path:
    api = api.strip().lower()
    return Path(shards_dir) / f"{theme_slug(theme)}.{api}.json"


def write_shard(
    shards_dir: Path,
    theme: str,
    api: str,
    items: list[dict[str, Any]],
) -> Path:
    """Write one theme×API shard atomically (single writer per file).

    Items are deduped (DOI → ISBN → normalized title) before write.
    """
    shards_dir = Path(shards_dir)
    shards_dir.mkdir(parents=True, exist_ok=True)
    path = shard_path(shards_dir, theme, api)
    deduped = merge_records([], items)
    payload = {
        "theme": theme,
        "api": api,
        "count": len(deduped),
        "items": deduped,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return path


def load_shard_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, list):
        return data
    return list(data.get("items") or [])


def collect_all_shard_items(shards_dir: Path) -> list[dict[str, Any]]:
    shards_dir = Path(shards_dir)
    if not shards_dir.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(shards_dir.glob("*.json")):
        if p.name.endswith(".tmp"):
            continue
        out.extend(load_shard_items(p))
    return out


def integrate_shards(
    candidates_path: Path,
    *,
    next_id: int | None = None,
    next_id_start: int = 1000,
) -> list[dict[str, Any]]:
    """Merge all shard files into candidates.json with dedupe.

    Keeps seeds / existing rows. Dedupe key: DOI → ISBN → normalized title
    (see `merge_records` / `record_key`).
    """
    shards = shards_dir_for(candidates_path)
    doc = load_candidates_doc(candidates_path, next_id_start=next_id_start)
    base = doc["items"]
    shard_items = collect_all_shard_items(shards)
    if not shard_items:
        return base
    nid = next_id if next_id is not None else int(doc.get("next_id") or next_id_start)
    # Explicit: merge_records dedupes across seeds + all theme×api shards
    merged = merge_records(base, shard_items)
    save_candidates(candidates_path, merged, next_id=nid)
    return merged


def assign_local_ids(
    items: list[dict[str, Any]],
    next_id: int,
    *,
    only_selected: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    """Assign monotonic local_id to items that lack one. Returns (items, new_next_id)."""
    nid = int(next_id)
    for rec in items:
        if only_selected and not is_accepted(rec):
            continue
        if rec.get("local_id") is None:
            rec["local_id"] = nid
            nid += 1
    return items, nid


def merge_records(
    existing: list[dict[str, Any]], new_items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for rec in existing + new_items:
        if not (rec.get("title") or rec.get("doi") or rec.get("isbn")):
            continue
        k = record_key(rec)
        if k in by_key:
            cur = by_key[k]
            if (rec.get("cited_by_count") or 0) > (cur.get("cited_by_count") or 0):
                cur["cited_by_count"] = rec["cited_by_count"]
            if len(rec.get("abstract") or "") > len(cur.get("abstract") or ""):
                cur["abstract"] = rec["abstract"]
            if not cur.get("doi") and rec.get("doi"):
                cur["doi"] = rec["doi"]
            if not cur.get("isbn") and rec.get("isbn"):
                cur["isbn"] = rec["isbn"]
            if not cur.get("openalex_id") and rec.get("openalex_id"):
                cur["openalex_id"] = rec["openalex_id"]
                cur["referenced_works"] = rec.get("referenced_works") or cur.get(
                    "referenced_works"
                )
            for fld in (
                "ai_score",
                "ai_review_path",
                "selected",
                "accepted",
                "local_id",
                "script_score",
                "decision",
                "reason",
                "notes",
            ):
                if rec.get(fld) is not None and cur.get(fld) is None:
                    cur[fld] = rec[fld]
            if rec.get("script_score") is not None:
                cur["script_score"] = max(cur.get("script_score") or 0, rec["script_score"])
        else:
            by_key[k] = dict(rec)
    items = list(by_key.values())
    items.sort(
        key=lambda r: (-(r.get("script_score") or 0), -(r.get("cited_by_count") or 0))
    )
    return items
