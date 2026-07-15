"""OpenAlex skip persistence across process restarts (UTC day)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from papers_library_pipeline import openalex_client, source_health


def setup_function():
    openalex_client.reset_rate_limit_state()
    source_health.reset_for_tests()


def teardown_function():
    openalex_client.reset_rate_limit_state()
    source_health.reset_for_tests()


def test_mark_rate_limited_persists_utc_day_skip(tmp_path: Path):
    path = tmp_path / "source-health.json"
    source_health.configure(path)
    now = datetime.now(timezone.utc)
    openalex_client.mark_rate_limited("HTTP 429")
    data = source_health.load()
    assert data["openalex_skip_until"] == source_health.utc_end_of_day(now).isoformat()
    assert "429" in data["openalex_skip_reason"]
    assert openalex_client.is_rate_limited()


def test_apply_persisted_skip_sets_process_flag(tmp_path: Path):
    path = tmp_path / "source-health.json"
    source_health.configure(path)
    now = datetime(2026, 7, 14, 12, 0, 0, tzinfo=timezone.utc)
    source_health.mark_openalex_skip_for_utc_day("budget", now=now)
    openalex_client.reset_rate_limit_state()

    with patch.object(
        source_health,
        "openalex_skip_active",
        return_value="budget",
    ):
        assert openalex_client.apply_persisted_skip() is True
    assert openalex_client.is_rate_limited()
    assert openalex_client.rate_limited_reason() == "budget"


def test_apply_persisted_skip_noop_when_expired(tmp_path: Path):
    path = tmp_path / "source-health.json"
    source_health.configure(path)
    source_health.save(
        {
            "openalex_skip_until": "2020-01-01T23:59:59+00:00",
            "openalex_skip_reason": "old",
        }
    )
    openalex_client.reset_rate_limit_state()
    assert openalex_client.apply_persisted_skip() is False
    assert not openalex_client.is_rate_limited()
    data = source_health.load()
    assert "openalex_skip_until" not in data


def test_search_works_returns_empty_when_limited():
    openalex_client.mark_rate_limited("limited", persist=False)
    with patch.object(openalex_client, "get_json") as gj:
        out = openalex_client.search_works("topic")
    assert out == []
    gj.assert_not_called()
