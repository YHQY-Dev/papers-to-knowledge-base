"""Resolve {ROOT}/{DOMAIN}-* paths from domain_config.json or env."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def find_config_path(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    env = os.environ.get("DOMAIN_KB_CONFIG")
    if env:
        return Path(env)
    cwd = Path.cwd() / "domain_config.json"
    if cwd.exists():
        return cwd
    raise FileNotFoundError(
        "No domain_config.json. Copy scripts/domain_config.example.json, "
        "edit it, and set DOMAIN_KB_CONFIG or run from that directory."
    )


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    path = find_config_path(config_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_config_path"] = str(path.resolve())
    root = Path(data["root"]).expanduser().resolve()
    domain = data["domain"]
    data["_root"] = root
    data["_domain"] = domain
    data["_pdf"] = root / f"{domain}-pdf"
    data["_md"] = root / f"{domain}-md"
    data["_catalog"] = root / f"{domain}-catalog"
    data["_candidates_dir"] = root / f"{domain}-candidates"
    data["_candidates"] = data["_candidates_dir"] / "candidates.json"
    data["_manifest"] = data["_catalog"] / "manifest.json"
    data["_ai_reviews"] = data["_catalog"] / "ai-reviews"
    data["_citation_extracts"] = data["_catalog"] / "citation-extracts"
    data["_manual_needed"] = data["_catalog"] / "manual-needed.md"
    data["_web"] = root / f"{domain}-web"
    data["_seed"] = root / f"{domain}-candidates" / "seed_works.json"
    return data


def ensure_dirs(cfg: dict[str, Any], *, include_site_dirs: bool = False) -> None:
    """Create library-stage dirs. Does not create md/web unless include_site_dirs=True."""
    keys = ("_pdf", "_catalog", "_candidates_dir", "_ai_reviews")
    if include_site_dirs:
        keys = keys + ("_md", "_web", "_citation_extracts")
    for key in keys:
        Path(cfg[key]).mkdir(parents=True, exist_ok=True)
