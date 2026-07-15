"""Tests for source_health persistence helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from papers_library_pipeline import source_health as sh


def test_utc_end_of_day():
    now = datetime(2026, 7, 14, 3, 4, 5, tzinfo=timezone.utc)
    end = sh.utc_end_of_day(now)
    assert end == datetime(2026, 7, 14, 23, 59, 59, tzinfo=timezone.utc)


def test_save_load_atomic(tmp_path: Path):
    path = tmp_path / "source-health.json"
    sh.configure(path)
    sh.save({"scihub_preferred": "https://sci-hub.st"})
    assert path.is_file()
    assert not (tmp_path / "source-health.json.tmp").exists()
    data = sh.load()
    assert data["scihub_preferred"] == "https://sci-hub.st"
    assert "updated_at" in data
    sh.reset_for_tests()


def test_openalex_skip_active_within_day(tmp_path: Path):
    path = tmp_path / "source-health.json"
    sh.configure(path)
    now = datetime(2026, 7, 14, 10, 0, 0, tzinfo=timezone.utc)
    sh.mark_openalex_skip_for_utc_day("429", now=now)
    assert sh.openalex_skip_active(now=now) == "429"
    next_day = datetime(2026, 7, 15, 0, 0, 1, tzinfo=timezone.utc)
    assert sh.openalex_skip_active(now=next_day) is None
    sh.reset_for_tests()


def test_mark_openalex_skip_does_not_shorten(tmp_path: Path):
    path = tmp_path / "source-health.json"
    sh.configure(path)
    later = datetime(2026, 7, 20, 23, 59, 59, tzinfo=timezone.utc)
    sh.save(
        {
            "openalex_skip_until": later.isoformat(),
            "openalex_skip_reason": "already",
        }
    )
    now = datetime(2026, 7, 14, 12, 0, 0, tzinfo=timezone.utc)
    sh.mark_openalex_skip_for_utc_day("new", now=now)
    data = sh.load()
    assert data["openalex_skip_until"] == later.isoformat()
    assert data["openalex_skip_reason"] == "already"
    sh.reset_for_tests()


def test_scihub_preferred_roundtrip(tmp_path: Path):
    path = tmp_path / "source-health.json"
    sh.configure(path)
    sh.set_scihub_preferred("https://sci-hub.st/")
    assert sh.get_scihub_preferred() == "https://sci-hub.st"
    sh.reset_for_tests()


def test_unconfigured_save_is_noop():
    sh.reset_for_tests()
    sh.save({"scihub_preferred": "https://sci-hub.st"})
    assert sh.load() == {}
