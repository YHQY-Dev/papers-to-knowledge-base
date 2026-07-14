from __future__ import annotations

import re
from typing import Any

from .http_util import get_json

OPENALEX = "https://api.openalex.org/works"


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
    params: dict[str, Any] = {
        "search": query,
        "per_page": per_page,
        "mailto": mailto,
        "sort": "cited_by_count:desc",
    }
    if typ:
        params["filter"] = f"type:{typ}"
    data = get_json(
        OPENALEX,
        params,
        user_agent=f"Domain-KB-Harvester/0.1 (mailto:{mailto})",
    )
    return [work_to_record(w) for w in data.get("results") or []]


def get_work_by_id(
    openalex_id: str, mailto: str = "kb-harvester@example.com"
) -> dict[str, Any] | None:
    wid = openalex_id.rstrip("/").split("/")[-1]
    try:
        data = get_json(
            f"{OPENALEX}/{wid}",
            {"mailto": mailto},
            user_agent=f"Domain-KB-Harvester/0.1 (mailto:{mailto})",
        )
        return work_to_record(data)
    except Exception:
        return None


def search_by_doi(
    doi: str, mailto: str = "kb-harvester@example.com"
) -> dict[str, Any] | None:
    doi = doi.lower().replace("https://doi.org/", "")
    try:
        data = get_json(
            OPENALEX,
            {"filter": f"doi:{doi}", "mailto": mailto},
            user_agent=f"Domain-KB-Harvester/0.1 (mailto:{mailto})",
        )
        results = data.get("results") or []
        return work_to_record(results[0]) if results else None
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
