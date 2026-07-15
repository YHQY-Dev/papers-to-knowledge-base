"""Incremental harvest persistence (shards + merge)."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from papers_library_pipeline.candidates import (
    collect_all_shard_items,
    integrate_shards,
    load_candidates_doc,
    merge_and_save,
    shard_path,
    write_shard,
)
from papers_library_pipeline import run_harvest


def test_merge_and_save_persists_after_each_batch(tmp_path: Path):
    path = tmp_path / "candidates.json"
    items: list = []
    items = merge_and_save(
        path,
        items,
        [{"doi": "10.1/a", "title": "A", "script_score": 1, "cited_by_count": 0}],
        next_id=1000,
    )
    assert path.is_file()
    doc1 = load_candidates_doc(path)
    assert doc1["count"] == 1
    assert doc1["next_id"] == 1000

    items = merge_and_save(
        path,
        items,
        [{"doi": "10.1/b", "title": "B", "script_score": 2, "cited_by_count": 0}],
        next_id=1000,
    )
    doc2 = json.loads(path.read_text(encoding="utf-8"))
    assert doc2["count"] == 2
    dois = {r["doi"] for r in doc2["items"]}
    assert dois == {"10.1/a", "10.1/b"}


def test_save_candidates_atomic_no_tmp_left(tmp_path: Path):
    path = tmp_path / "candidates.json"
    merge_and_save(
        path,
        [],
        [{"title": "Only", "doi": "10.1/x", "script_score": 0}],
        next_id=1,
    )
    assert path.is_file()
    assert not (tmp_path / "candidates.json.tmp").exists()


def test_write_shard_and_integrate(tmp_path: Path):
    cand = tmp_path / "candidates.json"
    shards = tmp_path / "shards"
    merge_and_save(
        cand,
        [],
        [{"doi": "10.seed/1", "title": "Seed", "script_score": 9}],
        next_id=1000,
    )
    write_shard(
        shards,
        "solid electrolyte",
        "openalex",
        [{"doi": "10.oa/1", "title": "OA", "script_score": 1}],
    )
    write_shard(
        shards,
        "solid electrolyte",
        "crossref",
        [{"doi": "10.cr/1", "title": "CR", "script_score": 2}],
    )
    assert shard_path(shards, "solid electrolyte", "openalex").is_file()
    assert len(collect_all_shard_items(shards)) == 2
    items = integrate_shards(cand, next_id=1000)
    dois = {r["doi"] for r in items}
    assert dois == {"10.seed/1", "10.oa/1", "10.cr/1"}


def test_integrate_shards_dedupes_same_doi(tmp_path: Path):
    cand = tmp_path / "candidates.json"
    shards = tmp_path / "shards"
    write_shard(
        shards,
        "theme a",
        "openalex",
        [
            {
                "doi": "10.1/same",
                "title": "From OA",
                "script_score": 10,
                "cited_by_count": 5,
                "abstract": "short",
            }
        ],
    )
    write_shard(
        shards,
        "theme b",
        "crossref",
        [
            {
                "doi": "10.1/same",
                "title": "From CR",
                "script_score": 40,
                "cited_by_count": 50,
                "abstract": "a much longer abstract that should win",
            }
        ],
    )
    # Duplicate inside one shard (same API typ noise)
    write_shard(
        shards,
        "theme a",
        "crossref",
        [
            {"doi": "10.2/x", "title": "Once", "script_score": 1},
            {"doi": "10.2/x", "title": "Once again", "script_score": 3},
        ],
    )
    items = integrate_shards(cand, next_id=1000)
    by_doi = {r["doi"]: r for r in items}
    assert len(items) == 2
    assert "10.1/same" in by_doi and "10.2/x" in by_doi
    assert by_doi["10.1/same"]["script_score"] == 40
    assert by_doi["10.1/same"]["cited_by_count"] == 50
    assert by_doi["10.2/x"]["script_score"] == 3


def test_harvest_theme_writes_separate_api_shards(tmp_path: Path, monkeypatch):
    shards = tmp_path / "shards"
    cfg = {
        "mailto": "u@example.org",
        "per_theme_limit": 5,
        "positive_keywords": [],
        "negative_cues": [],
    }

    started: list[str] = []
    first_sync = threading.Barrier(2, timeout=5)
    oa_once = threading.Event()
    cr_once = threading.Event()

    def fake_oa(theme, per_page=50, typ=None, mailto=""):
        started.append(f"oa:{typ}")
        if not oa_once.is_set():
            oa_once.set()
            first_sync.wait()
        return [
            {
                "source": "openalex",
                "doi": f"10.oa/{typ or 'any'}",
                "title": f"OA {typ}",
                "authors": [],
                "year": 2020,
                "type": typ or "article",
                "cited_by_count": 1,
                "abstract": "",
                "referenced_works": [],
            }
        ]

    def fake_cr(theme, rows=50, typ=None, mailto=""):
        started.append(f"cr:{typ}")
        if not cr_once.is_set():
            cr_once.set()
            first_sync.wait()
        return [
            {
                "source": "crossref",
                "doi": f"10.cr/{typ or 'any'}",
                "title": f"CR {typ}",
                "authors": [],
                "year": 2021,
                "type": typ or "article",
                "cited_by_count": 2,
                "abstract": "",
                "referenced_works": [],
            }
        ]

    monkeypatch.setattr(run_harvest.openalex_client, "search_works", fake_oa)
    monkeypatch.setattr(run_harvest.openalex_client, "is_rate_limited", lambda: False)
    monkeypatch.setattr(run_harvest.crossref_client, "search_works", fake_cr)
    monkeypatch.setattr(run_harvest.time, "sleep", lambda *_a, **_k: None)

    run_harvest.harvest_theme("solid electrolyte", cfg, shards_dir=shards)

    oa = shard_path(shards, "solid electrolyte", "openalex")
    cr = shard_path(shards, "solid electrolyte", "crossref")
    assert oa.is_file() and cr.is_file()
    # Accumulated all OA typs into one file (3), all CR typs into one (2)
    assert json.loads(oa.read_text(encoding="utf-8"))["count"] == 3
    assert json.loads(cr.read_text(encoding="utf-8"))["count"] == 2
    assert any(s.startswith("oa:") for s in started)
    assert any(s.startswith("cr:") for s in started)
