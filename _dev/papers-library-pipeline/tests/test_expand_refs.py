"""Tests for one-paper expand_refs."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from papers_library_pipeline import expand_refs
from papers_library_pipeline.candidates import load_candidates_doc, save_candidates


def test_pick_next_skips_expanded_and_empty():
    items = [
        {"doi": "10.1/a", "script_score": 90, "refs_expanded": True, "referenced_works": ["W1"]},
        {"doi": "10.1/b", "script_score": 80, "referenced_works": []},
        {"doi": "10.1/c", "script_score": 70, "referenced_works": ["W2"]},
    ]
    got = expand_refs.pick_next_source(items)
    assert got is not None
    assert got["doi"] == "10.1/c"


def test_expand_one_marks_source_and_merges(tmp_path: Path, monkeypatch):
    path = tmp_path / "candidates.json"
    items = [
        {
            "doi": "10.1/src",
            "title": "Src",
            "script_score": 50,
            "referenced_works": ["https://openalex.org/W99"],
        }
    ]
    save_candidates(path, items, next_id=1000)

    def fake_get(wid, mailto=""):
        return {
            "source": "openalex",
            "doi": "10.1/child",
            "title": "Child",
            "authors": [],
            "year": 2020,
            "type": "article",
            "cited_by_count": 1,
            "abstract": "",
            "referenced_works": [],
            "openalex_id": wid,
        }

    monkeypatch.setattr(expand_refs.openalex_client, "get_work_by_id", fake_get)
    monkeypatch.setattr(expand_refs.openalex_client, "is_rate_limited", lambda: False)
    monkeypatch.setattr(expand_refs.time, "sleep", lambda *_a, **_k: None)

    cfg = {"positive_keywords": [], "negative_cues": []}
    out = expand_refs.expand_one(items[0], items, cfg, path=path, next_id=1000)
    doc = load_candidates_doc(path)
    dois = {r["doi"] for r in doc["items"]}
    assert "10.1/src" in dois and "10.1/child" in dois
    src = next(r for r in doc["items"] if r["doi"] == "10.1/src")
    assert src.get("refs_expanded") is True
    assert len(out) >= 2
