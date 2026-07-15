#!/usr/bin/env python3
"""Harvest works from OpenAlex + Crossref into shard files / candidates.json.

Agent workflow (do NOT run everything in one process):

1. Optional once:  `run_harvest --seeds-only`
2. Per theme:      `run_harvest --theme "…"`   → writes shards only
3. After themes:   `run_harvest --integrate`  → dedupe-merge shards → candidates.json
4. Refs separately:`python -m papers_library_pipeline.expand_refs --next` (or --doi)

Within one --theme, OpenAlex ∥ Crossref write separate shard files.
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


def _setup(cfg_path: Path | None) -> tuple[dict[str, Any], Path, Path, int]:
    cfg = load_config(cfg_path)
    ensure_dirs(cfg)
    source_health.configure(Path(cfg["_source_health"]))
    openalex_client.apply_persisted_skip()
    start = int(cfg.get("next_id_start") or 1000)
    cand_path = Path(cfg["_candidates"])
    shards_dir = shards_dir_for(cand_path)
    shards_dir.mkdir(parents=True, exist_ok=True)
    return cfg, cand_path, shards_dir, start


def cmd_seeds_only(cfg: dict, cand_path: Path, next_id: int) -> int:
    doc = load_candidates_doc(cand_path, next_id_start=next_id)
    items = doc["items"]
    seed_path = Path(cfg["_seed"])
    if not seed_path.exists():
        print(f"no seed file at {seed_path}", file=sys.stderr)
        return 1
    seeds = json.loads(seed_path.read_text(encoding="utf-8"))
    if isinstance(seeds, dict):
        seeds = seeds.get("items") or seeds.get("seeds") or []
    for i, s in enumerate(seeds, start=1):
        items = merge_and_save(cand_path, items, [enrich_seed(s, cfg)], next_id=next_id)
        print(f"  [checkpoint] seed {i}/{len(seeds)} → {len(items)} candidates", flush=True)
    print(f"seeds done → {cand_path} ({len(items)} candidates)")
    return 0


def cmd_theme(cfg: dict, shards_dir: Path, theme: str) -> int:
    known = list(cfg.get("search_themes") or [])
    if known and theme not in known:
        print(
            f"[warn] theme not in domain_config search_themes: {theme!r}",
            file=sys.stderr,
        )
    print(f"harvest theme: {theme}", flush=True)
    harvest_theme(theme, cfg, shards_dir=shards_dir)
    print("theme harvest done (shards only; run --integrate after all themes)")
    return 0


def cmd_integrate(cand_path: Path, next_id: int, start: int) -> int:
    print("integrating shards → candidates.json (dedupe) …", flush=True)
    items = integrate_shards(cand_path, next_id=next_id, next_id_start=start)
    print(f"  [merge] {len(items)} candidates after deduped shard merge → {cand_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Harvest one theme into shards, or integrate shards. "
            "Do not expand references here — use papers_library_pipeline.expand_refs."
        )
    )
    ap.add_argument("--config", type=Path, default=None)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--theme",
        type=str,
        help="Harvest exactly one theme into shard files (OpenAlex∥Crossref)",
    )
    mode.add_argument(
        "--integrate",
        action="store_true",
        help="Merge all shards into candidates.json (dedupe); no API search",
    )
    mode.add_argument(
        "--seeds-only",
        action="store_true",
        help="Enrich seed_works.json into candidates.json once",
    )
    args = ap.parse_args()

    cfg, cand_path, shards_dir, start = _setup(args.config)
    doc = load_candidates_doc(cand_path, next_id_start=start)
    next_id = int(doc.get("next_id") or start)

    if args.seeds_only:
        return cmd_seeds_only(cfg, cand_path, next_id)
    if args.theme:
        return cmd_theme(cfg, shards_dir, args.theme.strip())
    if args.integrate:
        return cmd_integrate(cand_path, next_id, start)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
