from __future__ import annotations

import os
import re
import sys
from typing import Any

from .env_load import load_repo_env
from .http_util import HttpRateLimited, get_json
from . import source_health

load_repo_env()

OPENALEX = "https://api.openalex.org/works"

# Process-local: once daily budget / hard 429 hits, skip further OpenAlex calls.
_rate_limited_reason: str | None = None


def is_rate_limited() -> bool:
    return _rate_limited_reason is not None


def rate_limited_reason() -> str | None:
    return _rate_limited_reason


def mark_rate_limited(reason: str | BaseException, *, persist: bool = True) -> None:
    """Disable OpenAlex for the rest of this process (quota exhausted).

    When `persist` and source_health is configured, also skip OpenAlex until
    end of the current UTC day for subsequent runs.
    """
    global _rate_limited_reason
    reason_s = str(reason)
    if _rate_limited_reason is None:
        _rate_limited_reason = reason_s
        print(
            f"[openalex] rate/budget limited — skipping OpenAlex for this run; "
            f"using Crossref instead. ({_rate_limited_reason})",
            file=sys.stderr,
        )
    if persist and source_health.configured_path() is not None:
        source_health.mark_openalex_skip_for_utc_day(reason_s)


def apply_persisted_skip() -> bool:
    """Load source-health skip; if still active for UTC today, set process flag.

    Returns True if OpenAlex is skipped. Does not extend the deadline.
    """
    global _rate_limited_reason
    source_health.clear_expired_openalex_skip()
    reason = source_health.openalex_skip_active()
    if reason is None:
        return False
    if _rate_limited_reason is None:
        _rate_limited_reason = reason
        print(
            f"[openalex] skipped (persisted until UTC day end): {reason}",
            file=sys.stderr,
        )
    return True


def reset_rate_limit_state() -> None:
    """Test helper: clear the process-local skip flag."""
    global _rate_limited_reason
    _rate_limited_reason = None


def _api_key() -> str | None:
    key = (os.environ.get("OPENALEX_API_KEY") or "").strip()
    return key or None


def _auth_params(mailto: str = "kb-harvester@example.com") -> dict[str, Any]:
    """Prefer API key (current OpenAlex auth); keep mailto as polite fallback."""
    params: dict[str, Any] = {}
    key = _api_key()
    if key:
        params["api_key"] = key
    else:
        params["mailto"] = mailto
    return params


def _user_agent(mailto: str = "kb-harvester@example.com") -> str:
    return f"papers-library-pipeline/0.1 (mailto:{mailto})"


def _invert_abstract(inv: dict[str, list[int]] | None) -> str:
    if not inv:
        return ""
    size = max((i for idxs in inv.values() for i in idxs), default=-1) + 1
    words = [""] * size
    for w, idxs in inv.items():
        for i in idxs:
            if 0 <= i < size:
                words[i] = w
    return " ".join(words)


def _normalize_type(t: str | None) -> str:
    if not t:
        return "article"
    t = t.lower().replace(" ", "-")
    mapping = {
        "review": "review",
        "book": "book",
        "book-chapter": "book-chapter",
        "edited-book": "book",
        "monograph": "book",
        "article": "article",
        "journal-article": "article",
    }
    return mapping.get(t, t)


def work_to_record(w: dict[str, Any]) -> dict[str, Any]:
    doi = None
    ids = w.get("ids") or {}
    if ids.get("doi"):
        doi = ids["doi"].replace("https://doi.org/", "").lower()
    elif w.get("doi"):
        doi = str(w["doi"]).replace("https://doi.org/", "").lower()

    authorships = w.get("authorships") or []
    authors = []
    for a in authorships[:12]:
        name = (a.get("author") or {}).get("display_name")
        if name:
            authors.append(name)

    title = w.get("display_name") or w.get("title") or ""
    return {
        "source": "openalex",
        "openalex_id": w.get("id"),
        "doi": doi,
        "title": title,
        "authors": authors,
        "year": w.get("publication_year"),
        "type": _normalize_type(w.get("type")),
        "cited_by_count": w.get("cited_by_count") or 0,
        "abstract": _invert_abstract(w.get("abstract_inverted_index")),
        "referenced_works": w.get("referenced_works") or [],
        "isbn": None,
        "language": w.get("language"),
    }


def search_works(
    query: str,
    per_page: int = 50,
    typ: str | None = None,
    mailto: str = "kb-harvester@example.com",
) -> list[dict[str, Any]]:
    if is_rate_limited():
        return []
    params: dict[str, Any] = {
        "search": query,
        "per_page": per_page,
        "sort": "cited_by_count:desc",
        **_auth_params(mailto),
    }
    if typ:
        params["filter"] = f"type:{typ}"
    try:
        data = get_json(OPENALEX, params, user_agent=_user_agent(mailto))
    except HttpRateLimited as e:
        mark_rate_limited(e)
        return []
    return [work_to_record(w) for w in data.get("results") or []]


def get_work_by_id(
    openalex_id: str, mailto: str = "kb-harvester@example.com"
) -> dict[str, Any] | None:
    if is_rate_limited():
        return None
    wid = openalex_id.rstrip("/").split("/")[-1]
    try:
        data = get_json(
            f"{OPENALEX}/{wid}",
            _auth_params(mailto),
            user_agent=_user_agent(mailto),
        )
        return work_to_record(data)
    except HttpRateLimited as e:
        mark_rate_limited(e)
        return None
    except Exception:
        return None


def search_by_doi(
    doi: str, mailto: str = "kb-harvester@example.com"
) -> dict[str, Any] | None:
    if is_rate_limited():
        return None
    doi = doi.lower().replace("https://doi.org/", "")
    try:
        data = get_json(
            OPENALEX,
            {"filter": f"doi:{doi}", **_auth_params(mailto)},
            user_agent=_user_agent(mailto),
        )
        results = data.get("results") or []
        return work_to_record(results[0]) if results else None
    except HttpRateLimited as e:
        mark_rate_limited(e)
        return None
    except Exception:
        return None


def search_by_title(
    title: str, mailto: str = "kb-harvester@example.com"
) -> dict[str, Any] | None:
    hits = search_works(title, per_page=5, mailto=mailto)
    if not hits:
        return None
    nt = re.sub(r"\W+", " ", title.lower()).strip()
    for h in hits:
        ht = re.sub(r"\W+", " ", (h.get("title") or "").lower()).strip()
        if nt and (nt in ht or ht in nt):
            return h
    return hits[0]
