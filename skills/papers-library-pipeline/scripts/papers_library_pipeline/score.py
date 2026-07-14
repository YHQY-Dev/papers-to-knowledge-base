from __future__ import annotations

import math
import re
from typing import Any


DEFAULT_TYPE_BONUS = {
    "book": 35,
    "monograph": 35,
    "edited-book": 30,
    "review": 30,
    "book-chapter": 20,
    "book-section": 20,
    "article": 5,
    "journal-article": 5,
    "proceedings-article": 0,
}


def script_score(rec: dict[str, Any], cfg: dict[str, Any] | None = None) -> int:
    cfg = cfg or {}
    type_bonus = cfg.get("type_bonus") or DEFAULT_TYPE_BONUS
    positive = [k.lower() for k in (cfg.get("positive_keywords") or [])]
    negative = [k.lower() for k in (cfg.get("negative_cues") or [])]

    score = 0
    typ = (rec.get("type") or "article").lower()
    score += int(type_bonus.get(typ, 5))

    text = f"{rec.get('title') or ''} {rec.get('abstract') or ''}".lower()
    if positive:
        hits = sum(1 for kw in positive if kw in text)
        score += min(25, hits * 4)

    cites = int(rec.get("cited_by_count") or 0)
    if cites > 0:
        score += min(25, int(math.log10(cites + 1) * 10))

    if typ in {"article", "journal-article"} and re.search(
        r"\breview\b|综述", text
    ):
        score += 20

    if negative:
        neg = sum(1 for cue in negative if cue in text)
        score -= min(40, neg * 15)

    return int(max(0, min(100, score)))
