"""Sci-Hub preferred mirror: probe once, reuse across downloads."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from papers_library_pipeline import pdf_fetch, source_health


def setup_function():
    pdf_fetch.reset_mirror_session_state()
    source_health.reset_for_tests()


def teardown_function():
    pdf_fetch.reset_mirror_session_state()
    source_health.reset_for_tests()


def test_order_sources_puts_preferred_first():
    ordered = pdf_fetch._order_sources(
        "https://sci-hub.st",
        ["https://sci-hub.al", "https://sci-hub.st", "https://sci-hub.ru"],
    )
    assert ordered[0] == "https://sci-hub.st"
    assert ordered == ["https://sci-hub.st", "https://sci-hub.al", "https://sci-hub.ru"]


def test_ensure_mirror_order_probes_preferred_once(tmp_path: Path):
    health = tmp_path / "source-health.json"
    source_health.configure(health)
    source_health.set_scihub_preferred("https://sci-hub.st")

    calls: list[str] = []

    def fake_probe(url, client=None):
        calls.append(pdf_fetch._normalize_mirror(url))
        return url.rstrip("/") == "https://sci-hub.st"

    with patch.object(pdf_fetch, "probe_mirror", side_effect=fake_probe):
        first = pdf_fetch.ensure_mirror_order()
        second = pdf_fetch.ensure_mirror_order()

    assert first[0] == "https://sci-hub.st"
    assert second[0] == "https://sci-hub.st"
    assert calls == ["https://sci-hub.st"]  # probed once


def test_ensure_mirror_order_finds_first_alive_when_no_preferred(tmp_path: Path):
    health = tmp_path / "source-health.json"
    source_health.configure(health)

    def fake_probe(url, client=None):
        return url.rstrip("/") == "https://sci-hub.ee"

    with patch.object(pdf_fetch, "probe_mirror", side_effect=fake_probe):
        ordered = pdf_fetch.ensure_mirror_order()

    assert ordered[0] == "https://sci-hub.ee"
    assert source_health.get_scihub_preferred() == "https://sci-hub.ee"


def test_search_paper_by_doi_uses_preferred_and_persists(tmp_path: Path):
    health = tmp_path / "source-health.json"
    source_health.configure(health)
    source_health.set_scihub_preferred("https://sci-hub.st")
    pdf_fetch._session_ordered_sources = pdf_fetch._order_sources("https://sci-hub.st")
    pdf_fetch._session_preferred = "https://sci-hub.st"
    pdf_fetch._session_probed = True

    html = '<embed src="//sci-hub.st/downloads/paper.pdf">'
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "text/html"}
    mock_resp.content = b"<html>"
    mock_resp.text = html
    mock_resp.url = "https://sci-hub.st/10.1/x"

    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp
    mock_client.__enter__ = lambda s: mock_client
    mock_client.__exit__ = MagicMock(return_value=False)

    with (
        patch.object(pdf_fetch, "_fetch_crossref_metadata", return_value={"title": "T"}),
        patch.object(pdf_fetch, "resolve_oa_pdf_url", return_value=None),
        patch.object(pdf_fetch, "_client", return_value=mock_client),
    ):
        result = pdf_fetch.search_paper_by_doi("10.1/x")

    assert result["status"] == "success"
    assert result["source"] == "mirror:https://sci-hub.st"
    assert source_health.get_scihub_preferred() == "https://sci-hub.st"
    # Only tried preferred first (one GET)
    assert mock_client.get.call_count == 1
