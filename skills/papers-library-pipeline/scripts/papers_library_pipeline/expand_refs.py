#!/usr/bin/env python3
"""Expand OpenAlex referenced_works for ONE source paper at a time.

Separate from theme harvest. Agent should call this once per paper, e.g.:

  uv run python -m papers_library_pipeline.expand_refs --next
  uv run python -m papers_library_pipeline.expand_refs --doi 10.1016/...

Each run expands at most one seed paper's references into candidates.json
and marks that paper `refs_expanded=true` so `--next` advances.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

_PKG = Path(__file__).resolve().parents[1]
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from papers_library_pipeline import openalex_client
from papers_library_pipeline.candidates import (
    load_candidates_doc,
    merge_and_save,
    record_key,
    save_candidates,
)
from papers_library_pipeline.paths import ensure_dirs, load_config
from papers_library_pipeline.score import script_score
from papers_library_pipeline import source_health


def _norm_doi(doi: str | None) -> str:
    return (doi or "").lower().replace("https://doi.org/", "").strip()


def pick_next_source(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    ranked = sorted(items, key=lambda r: -(r.get("script_score") or 0))
    for rec in ranked:
        if rec.get("refs_expanded"):
            continue
        refs = rec.get("referenced_works") or []
        if not refs:
            continue
        return rec
    return None


def find_by_doi(items: list[dict[str, Any]], doi: str) -> dict[str, Any] | None:
    want = _norm_doi(doi)
    for rec in items:
        if _norm_doi(rec.get("doi")) == want:
            return rec
    return None


def expand_one(
    source: dict[str, Any],
    items: list[dict[str, Any]],
    cfg: dict[str, Any],
    *,
    path: Path,
    next_id: int,
    max_refs: int = 40,
) -> list[dict[str, Any]]:
    if openalex_client.is_rate_limited():
        print(
            "[openalex] rate-limited — skip expand_refs for this call",
            file=sys.stderr,
        )
        return items
    mailto = cfg.get("mailto") or "kb-harvester@example.com"
    refs = list(source.get("referenced_works") or [])[:max_refs]
    label = source.get("doi") or source.get("title") or record_key(source)
    print(f"expand refs from {label!r} ({len(refs)} ids) …", flush=True)
    seen_ids: set[str] = set()
    added = 0
    for wid in refs:
        if openalex_client.is_rate_limited():
            break
        if wid in seen_ids:
            continue
        seen_ids.add(wid)
        got = openalex_client.get_work_by_id(wid, mailto=mailto)
        if got:
            got["script_score"] = script_score(got, cfg)
            got["from_reference_of"] = source.get("doi") or source.get("title")
            items = merge_and_save(path, items, [got], next_id=next_id)
            added += 1
        time.sleep(0.35)

    # Mark source in the current items list (same object may have been replaced on merge)
    src_key = record_key(source)
    for rec in items:
        if record_key(rec) == src_key:
            rec["refs_expanded"] = True
            break
    else:
        source["refs_expanded"] = True
        items = merge_and_save(path, items, [source], next_id=next_id)

    save_candidates(path, items, next_id=next_id)
    print(
        f"  [refs] done from {label!r}: +{added} works → {len(items)} candidates",
        flush=True,
    )
    return items


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Expand references for one paper (not part of theme harvest)"
    )
    ap.add_argument("--config", type=Path, default=None)
    pick = ap.add_mutually_exclusive_group(required=True)
    pick.add_argument("--doi", type=str, help="Expand refs of this DOI")
    pick.add_argument(
        "--next",
        action="store_true",
        help="Expand refs of the next highest-scoring paper not yet refs_expanded",
    )
    ap.add_argument(
        "--max-refs",
        type=int,
        default=40,
        help="Max referenced_works ids to fetch for this one paper (default 40)",
    )
    args = ap.parse_args()

    cfg = load_config(args.config)
    ensure_dirs(cfg)
    source_health.configure(Path(cfg["_source_health"]))
    openalex_client.apply_persisted_skip()

    start = int(cfg.get("next_id_start") or 1000)
    cand_path = Path(cfg["_candidates"])
    doc = load_candidates_doc(cand_path, next_id_start=start)
    items = doc["items"]
    next_id = int(doc.get("next_id") or start)

    if not items:
        print("candidates.json empty — integrate harvest shards first", file=sys.stderr)
        return 1

    if args.doi:
        source = find_by_doi(items, args.doi)
        if source is None:
            print(f"DOI not in candidates: {args.doi}", file=sys.stderr)
            return 1
    else:
        source = pick_next_source(items)
        if source is None:
            print("no more papers with referenced_works left to expand")
            return 0

    if not (source.get("referenced_works") or []):
        print("chosen paper has no referenced_works", file=sys.stderr)
        source["refs_expanded"] = True
        save_candidates(cand_path, items, next_id=next_id)
        return 1

    expand_one(
        source,
        items,
        cfg,
        path=cand_path,
        next_id=next_id,
        max_refs=args.max_refs,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
