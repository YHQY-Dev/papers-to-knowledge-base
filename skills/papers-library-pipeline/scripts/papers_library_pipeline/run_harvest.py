#!/usr/bin/env python3
"""Harvest works from OpenAlex + Crossref into {DOMAIN}-candidates/candidates.json.

Each theme×API writes its own shard under {DOMAIN}-candidates/shards/
(e.g. solid_electrolyte.ab12cd34.openalex.json). OpenAlex and Crossref for the
same theme may run in parallel because they never share a file. After all themes
finish, shards are merged once into candidates.json (seeds already there kept).

Themes stay sequential to limit OpenAlex daily budget burn.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# Allow: python -m papers_library_pipeline.run_harvest  OR  python run_harvest.py
_PKG = Path(__file__).resolve().parents[1]
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from papers_library_pipeline import crossref_client, openalex_client
from papers_library_pipeline.candidates import (
    integrate_shards,
    load_candidates_doc,
    merge_and_save,
    shards_dir_for,
    write_shard,
)
from papers_library_pipeline.paths import ensure_dirs, load_config
from papers_library_pipeline.score import script_score
from papers_library_pipeline import source_health


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


def _tag_theme(recs: list[dict[str, Any]], theme: str, cfg: dict) -> list[dict[str, Any]]:
    for rec in recs:
        rec["script_score"] = script_score(rec, cfg)
        rec["harvest_theme"] = theme
    return recs


def _harvest_openalex(
    theme: str,
    cfg: dict,
    *,
    shards_dir: Path,
) -> Path | None:
    mailto = cfg.get("mailto") or "kb-harvester@example.com"
    limit = int(cfg.get("per_theme_limit") or 40)
    collected: list[dict[str, Any]] = []
    out_path: Path | None = None
    for typ in ("review", "book", None):
        if openalex_client.is_rate_limited():
            break
        try:
            batch = openalex_client.search_works(
                theme, per_page=limit, typ=typ, mailto=mailto
            )
            if batch:
                collected.extend(_tag_theme(batch, theme, cfg))
                out_path = write_shard(shards_dir, theme, "openalex", collected)
                print(
                    f"  [shard] openalex typ={typ!r} → {len(collected)} items",
                    flush=True,
                )
        except Exception as e:
            print(f"[openalex] theme={theme!r} typ={typ}: {e}", file=sys.stderr)
        if openalex_client.is_rate_limited():
            break
        time.sleep(1.0)
    return out_path


def _harvest_crossref(
    theme: str,
    cfg: dict,
    *,
    shards_dir: Path,
) -> Path | None:
    mailto = cfg.get("mailto") or "kb-harvester@example.com"
    limit = int(cfg.get("per_theme_limit") or 40)
    collected: list[dict[str, Any]] = []
    out_path: Path | None = None
    for typ in ("book", None):
        try:
            batch = crossref_client.search_works(
                theme, rows=limit, typ=typ, mailto=mailto
            )
            if batch:
                collected.extend(_tag_theme(batch, theme, cfg))
                out_path = write_shard(shards_dir, theme, "crossref", collected)
                print(
                    f"  [shard] crossref typ={typ!r} → {len(collected)} items",
                    flush=True,
                )
        except Exception as e:
            print(f"[crossref] theme={theme!r} typ={typ}: {e}", file=sys.stderr)
        time.sleep(1.2)
    return out_path


def harvest_theme(
    theme: str,
    cfg: dict,
    *,
    shards_dir: Path,
) -> None:
    """Search one theme; OpenAlex ∥ Crossref each write their own shard file."""
    shards_dir = Path(shards_dir)
    shards_dir.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(_harvest_openalex, theme, cfg, shards_dir=shards_dir),
            pool.submit(_harvest_crossref, theme, cfg, shards_dir=shards_dir),
        ]
        for fut in as_completed(futures):
            fut.result()
    print(f"  [shard] theme complete {theme!r}", flush=True)


def expand_references(
    items: list[dict[str, Any]],
    cfg: dict,
    *,
    path: Path,
    next_id: int,
) -> list[dict[str, Any]]:
    """Expand OpenAlex referenced_works; save after each fetched work."""
    if openalex_client.is_rate_limited():
        print(
            "[openalex] skip reference expand (rate-limited); candidates still from Crossref",
            file=sys.stderr,
        )
        return items
    mailto = cfg.get("mailto") or "kb-harvester@example.com"
    top_n = int(cfg.get("reference_expand_top") or 15)
    ranked = sorted(items, key=lambda r: -(r.get("script_score") or 0))
    seen_ids: set[str] = set()
    count = 0
    for rec in ranked:
        if openalex_client.is_rate_limited():
            break
        refs = rec.get("referenced_works") or []
        if not refs:
            continue
        count += 1
        if count > top_n:
            break
        for wid in refs[:40]:
            if openalex_client.is_rate_limited():
                break
            if wid in seen_ids:
                continue
            seen_ids.add(wid)
            got = openalex_client.get_work_by_id(wid, mailto=mailto)
            if got:
                got["script_score"] = script_score(got, cfg)
                got["from_reference_of"] = rec.get("doi") or rec.get("title")
                items = merge_and_save(path, items, [got], next_id=next_id)
            time.sleep(0.35)
        print(
            f"  [checkpoint] refs from {rec.get('doi') or rec.get('title')!r} "
            f"→ {len(items)} candidates",
            flush=True,
        )
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--skip-refs", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    ensure_dirs(cfg)
    source_health.configure(Path(cfg["_source_health"]))
    openalex_client.apply_persisted_skip()

    start = int(cfg.get("next_id_start") or 1000)
    cand_path = Path(cfg["_candidates"])
    shards_dir = shards_dir_for(cand_path)
    shards_dir.mkdir(parents=True, exist_ok=True)

    doc = load_candidates_doc(cand_path, next_id_start=start)
    items = doc["items"]
    next_id = int(doc.get("next_id") or start)

    seed_path = Path(cfg["_seed"])
    if seed_path.exists():
        seeds = json.loads(seed_path.read_text(encoding="utf-8"))
        if isinstance(seeds, dict):
            seeds = seeds.get("items") or seeds.get("seeds") or []
        for i, s in enumerate(seeds, start=1):
            items = merge_and_save(cand_path, items, [enrich_seed(s, cfg)], next_id=next_id)
            print(f"  [checkpoint] seed {i}/{len(seeds)} → {len(items)} candidates", flush=True)

    themes = list(cfg.get("search_themes") or [])
    for theme in themes:
        print(f"harvest theme: {theme}", flush=True)
        harvest_theme(theme, cfg, shards_dir=shards_dir)

    print("integrating shards → candidates.json (dedupe) …", flush=True)
    items = integrate_shards(cand_path, next_id=next_id, next_id_start=start)
    print(f"  [merge] {len(items)} candidates after deduped shard merge", flush=True)

    if not args.skip_refs:
        print("expand references…", flush=True)
        items = expand_references(
            items, cfg, path=cand_path, next_id=next_id
        )

    print(f"wrote {len(items)} candidates → {cand_path} (next_id={next_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
