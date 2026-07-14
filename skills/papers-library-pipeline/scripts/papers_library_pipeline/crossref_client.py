from __future__ import annotations

import re
from typing import Any

from .http_util import get_json

CROSSREF = "https://api.crossref.org/works"


def _normalize_type(t: str | None) -> str:
    if not t:
        return "article"
    t = t.lower()
    mapping = {
        "book": "book",
        "edited-book": "book",
        "monograph": "book",
        "book-chapter": "book-chapter",
        "journal-article": "article",
        "proceedings-article": "proceedings-article",
        "dissertation": "book",
        "reference-book": "book",
    }
    return mapping.get(t, t)


def item_to_record(item: dict[str, Any]) -> dict[str, Any]:
    title_l = item.get("title") or []
    title = title_l[0] if title_l else ""
    authors = []
    for a in (item.get("author") or [])[:12]:
        given = a.get("given") or ""
        family = a.get("family") or ""
        name = f"{given} {family}".strip() or a.get("name")
        if name:
            authors.append(name)
    year = None
    for key in ("published-print", "published-online", "created"):
        parts = ((item.get(key) or {}).get("date-parts") or [[None]])[0]
        if parts and parts[0]:
            year = parts[0]
            break
    isbn = None
    isbns = item.get("ISBN") or []
    if isbns:
        isbn = isbns[0]
    subtype = (item.get("subtype") or "").lower()
    typ = _normalize_type(item.get("type"))
    if "review" in subtype or "review" in title.lower():
        typ = "review"
    return {
        "source": "crossref",
        "openalex_id": None,
        "doi": (item.get("DOI") or "").lower() or None,
        "title": title,
        "authors": authors,
        "year": year,
        "type": typ,
        "cited_by_count": item.get("is-referenced-by-count") or 0,
        "abstract": re.sub(r"<[^>]+>", " ", item.get("abstract") or ""),
        "referenced_works": [],
        "isbn": isbn,
        "language": None,
    }


def search_works(
    query: str,
    rows: int = 50,
    typ: str | None = None,
    mailto: str = "kb-harvester@example.com",
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "query": query,
        "rows": rows,
        "mailto": mailto,
    }
    if typ:
        params["filter"] = f"type:{typ}"
    data = get_json(
        CROSSREF,
        params,
        user_agent=f"Domain-KB-Harvester/0.1 (mailto:{mailto})",
    )
    items = ((data.get("message") or {}).get("items")) or []
    return [item_to_record(it) for it in items]


def get_by_doi(
    doi: str, mailto: str = "kb-harvester@example.com"
) -> dict[str, Any] | None:
    doi = doi.lower().replace("https://doi.org/", "")
    try:
        data = get_json(
            f"{CROSSREF}/{doi}",
            {"mailto": mailto},
            user_agent=f"Domain-KB-Harvester/0.1 (mailto:{mailto})",
        )
        msg = data.get("message")
        return item_to_record(msg) if msg else None
    except Exception:
        return None


def search_by_title(
    title: str, mailto: str = "kb-harvester@example.com"
) -> dict[str, Any] | None:
    hits = search_works(title, rows=5, mailto=mailto)
    if not hits:
        return None
    nt = re.sub(r"\W+", " ", title.lower()).strip()
    for h in hits:
        ht = re.sub(r"\W+", " ", (h.get("title") or "").lower()).strip()
        if nt and (nt in ht or ht in nt):
            return h
    return hits[0]
