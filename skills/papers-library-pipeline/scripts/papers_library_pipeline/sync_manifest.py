#!/usr/bin/env python3
"""Sync {DOMAIN}-catalog/manifest.json from PDF on disk (optional MD)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1]
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from papers_library_pipeline.candidates import load_candidates
from papers_library_pipeline.manifest import sync_from_disk
from papers_library_pipeline.paths import load_config


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Rebuild catalog manifest from PDF disk (A-stage; MD optional)"
    )
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument(
        "--include-md",
        action="store_true",
        help="Also scan {DOMAIN}-md/ if it already exists (does not create it)",
    )
    args = ap.parse_args()
    cfg = load_config(args.config)
    start = int(cfg.get("next_id_start") or 1000)
    items = load_candidates(cfg["_candidates"])
    md_dir = Path(cfg["_md"]) if args.include_md else None
    man = sync_from_disk(
        Path(cfg["_manifest"]),
        Path(cfg["_pdf"]),
        md_dir=md_dir,
        candidates=items,
        next_id_start=start,
    )
    print(
        json.dumps(
            {
                "manifest": str(cfg["_manifest"]),
                "items": len(man.get("items") or []),
                "include_md": bool(args.include_md),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
