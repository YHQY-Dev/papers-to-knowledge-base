"""Incremental harvest persistence (merge_and_save / atomic write)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from papers_library_pipeline.candidates import load_candidates_doc, merge_and_save
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


def test_harvest_theme_checkpoints_per_api_batch(tmp_path: Path, monkeypatch):
    path = tmp_path / "candidates.json"
    cfg = {
        "mailto": "u@example.org",
        "per_theme_limit": 5,
        "positive_keywords": [],
        "negative_cues": [],
    }

    def fake_oa(theme, per_page=50, typ=None, mailto=""):
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

    writes: list[int] = []
    real_merge = run_harvest.merge_and_save

    def counting_merge(p, existing, new_items, *, next_id=None):
        out = real_merge(p, existing, new_items, next_id=next_id)
        writes.append(len(out))
        return out

    with patch.object(run_harvest, "merge_and_save", side_effect=counting_merge):
        items = run_harvest.harvest_theme(
            "solid electrolyte",
            cfg,
            path=path,
            items=[],
            next_id=1000,
        )

    # 3 OpenAlex typ + 2 Crossref typ = 5 checkpoints
    assert len(writes) == 5
    assert path.is_file()
    assert len(items) >= 2
