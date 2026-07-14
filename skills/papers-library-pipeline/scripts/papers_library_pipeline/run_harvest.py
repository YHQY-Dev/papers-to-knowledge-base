#!/usr/bin/env python3
"""Harvest works from OpenAlex + Crossref into {DOMAIN}-candidates/candidates.json."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Allow: python -m papers_library_pipeline.run_harvest  OR  python run_harvest.py
_PKG = Path(__file__).resolve().parents[1]
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from papers_library_pipeline import crossref_client, openalex_client
from papers_library_pipeline.candidates import (
    load_candidates_doc,
    merge_records,
    save_candidates,
)
from papers_library_pipeline.paths import ensure_dirs, load_config
from papers_library_pipeline.score import script_score


def enrich_seed(seed: dict, cfg: dict) -> dict:
    mailto = cfg.get("mailto") or "kb-harvester@example.com"
    rec = {
        "source": "seed",
        "doi": (seed.get("doi") or None),
        "title": seed.get("title"),
        "authors": seed.get("authors") or [],
        "year": seed.get("year"),
        "type": seed.get("type") or "article",
        "isbn": seed.get("isbn"),
        "cited_by_count": seed.get("cited_by_count") or 0,
        "abstract": seed.get("notes") or "",
        "referenced_works": [],
        "local_id": seed.get("local_id"),
        "language": seed.get("language"),
        "from_seed": True,
    }
    resolved = None
    if rec["doi"]:
        resolved = openalex_client.search_by_doi(rec["doi"], mailto=mailto) or (
            crossref_client.get_by_doi(rec["doi"], mailto=mailto)
        )
    if not resolved and rec["title"]:
        resolved = openalex_client.search_by_title(rec["title"], mailto=mailto) or (
            crossref_client.search_by_title(rec["title"], mailto=mailto)
        )
    if resolved:
        for k, v in resolved.items():
            if v and not rec.get(k):
                rec[k] = v
            elif k in {"abstract", "cited_by_count", "referenced_works", "openalex_id"} and v:
                rec[k] = v
        if resolved.get("type"):
            rec["type"] = seed.get("type") or resolved["type"]
    rec["script_score"] = script_score(rec, cfg)
    return rec


def harvest_theme(theme: str, cfg: dict) -> list[dict]:
    mailto = cfg.get("mailto") or "kb-harvester@example.com"
    limit = int(cfg.get("per_theme_limit") or 40)
    items: list[dict] = []
    for typ in ("review", "book", None):
        try:
            items.extend(
                openalex_client.search_works(theme, per_page=limit, typ=typ, mailto=mailto)
            )
        except Exception as e:
            print(f"[openalex] theme={theme!r} typ={typ}: {e}", file=sys.stderr)
        time.sleep(1.0)
    for typ in ("book", None):
        try:
            items.extend(
                crossref_client.search_works(theme, rows=limit, typ=typ, mailto=mailto)
            )
        except Exception as e:
            print(f"[crossref] theme={theme!r} typ={typ}: {e}", file=sys.stderr)
        time.sleep(1.2)
    for rec in items:
        rec["script_score"] = script_score(rec, cfg)
        rec["harvest_theme"] = theme
    return items


def expand_references(items: list[dict], cfg: dict) -> list[dict]:
    mailto = cfg.get("mailto") or "kb-harvester@example.com"
    top_n = int(cfg.get("reference_expand_top") or 15)
    ranked = sorted(items, key=lambda r: -(r.get("script_score") or 0))
    expanded: list[dict] = []
    seen_ids: set[str] = set()
    count = 0
    for rec in ranked:
        refs = rec.get("referenced_works") or []
        if not refs:
            continue
        count += 1
        if count > top_n:
            break
        for wid in refs[:40]:
            if wid in seen_ids:
                continue
            seen_ids.add(wid)
            got = openalex_client.get_work_by_id(wid, mailto=mailto)
            if got:
                got["script_score"] = script_score(got, cfg)
                got["from_reference_of"] = rec.get("doi") or rec.get("title")
                expanded.append(got)
            time.sleep(0.35)
    return expanded


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--skip-refs", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    ensure_dirs(cfg)

    start = int(cfg.get("next_id_start") or 1000)
    doc = load_candidates_doc(cfg["_candidates"], next_id_start=start)
    existing = doc["items"]
    next_id = int(doc.get("next_id") or start)
    batch: list[dict] = []

    seed_path = Path(cfg["_seed"])
    if seed_path.exists():
        seeds = json.loads(seed_path.read_text(encoding="utf-8"))
        if isinstance(seeds, dict):
            seeds = seeds.get("items") or seeds.get("seeds") or []
        for s in seeds:
            batch.append(enrich_seed(s, cfg))

    for theme in cfg.get("search_themes") or []:
        print(f"harvest theme: {theme}")
        batch.extend(harvest_theme(theme, cfg))

    merged = merge_records(existing, batch)
    if not args.skip_refs:
        print("expand references…")
        merged = merge_records(merged, expand_references(merged, cfg))

    save_candidates(cfg["_candidates"], merged, next_id=next_id)
    print(f"wrote {len(merged)} candidates → {cfg['_candidates']} (next_id={next_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
