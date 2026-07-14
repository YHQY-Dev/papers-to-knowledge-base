"""Offline unit tests: parsing + request param wiring (mocked HTTP)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from papers_library_pipeline import crossref_client, openalex_client
from papers_library_pipeline.http_util import HttpRateLimited, get_json


def test_openalex_work_to_record_inverts_abstract_and_doi():
    w = {
        "id": "https://openalex.org/W123",
        "display_name": "Example Work",
        "ids": {"doi": "https://doi.org/10.1000/xyz"},
        "publication_year": 2020,
        "type": "journal-article",
        "cited_by_count": 3,
        "authorships": [{"author": {"display_name": "Ada Lovelace"}}],
        "abstract_inverted_index": {"Hello": [0], "world": [1]},
        "referenced_works": [],
        "language": "en",
    }
    rec = openalex_client.work_to_record(w)
    assert rec["doi"] == "10.1000/xyz"
    assert rec["title"] == "Example Work"
    assert rec["type"] == "article"
    assert rec["authors"] == ["Ada Lovelace"]
    assert rec["abstract"] == "Hello world"
    assert rec["source"] == "openalex"


def test_crossref_item_to_record_strips_html_abstract():
    item = {
        "DOI": "10.1000/abc",
        "title": ["A Crossref Title"],
        "author": [{"given": "Grace", "family": "Hopper"}],
        "type": "journal-article",
        "published-print": {"date-parts": [[2019, 1, 1]]},
        "is-referenced-by-count": 11,
        "abstract": "<jats:p>Hello <i>world</i></jats:p>",
        "ISBN": [],
    }
    rec = crossref_client.item_to_record(item)
    assert rec["doi"] == "10.1000/abc"
    assert rec["year"] == 2019
    assert rec["authors"] == ["Grace Hopper"]
    assert "Hello" in rec["abstract"]
    assert "<" not in rec["abstract"]
    assert rec["source"] == "crossref"


def test_openalex_search_by_doi_uses_api_key_when_set(monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", "test-key-123")
    captured: dict = {}

    def fake_get_json(url, params=None, retries=4, user_agent=""):
        captured["url"] = url
        captured["params"] = dict(params or {})
        return {
            "results": [
                {
                    "id": "https://openalex.org/W1",
                    "display_name": "Keyed",
                    "ids": {"doi": "https://doi.org/10.1/x"},
                    "publication_year": 2021,
                    "type": "article",
                    "cited_by_count": 0,
                    "authorships": [],
                }
            ]
        }

    with patch.object(openalex_client, "get_json", side_effect=fake_get_json):
        rec = openalex_client.search_by_doi("10.1/x")
    assert rec is not None
    assert rec["title"] == "Keyed"
    assert captured["params"].get("api_key") == "test-key-123"
    assert "mailto" not in captured["params"]


def test_crossref_get_by_doi_calls_works_endpoint():
    captured: dict = {}

    def fake_get_json(url, params=None, retries=4, user_agent=""):
        captured["url"] = url
        return {
            "message": {
                "DOI": "10.5555/123",
                "title": ["CR Title"],
                "author": [],
                "type": "journal-article",
                "created": {"date-parts": [[2022]]},
            }
        }

    with patch.object(crossref_client, "get_json", side_effect=fake_get_json):
        rec = crossref_client.get_by_doi("10.5555/123")
    assert rec is not None
    assert rec["title"] == "CR Title"
    assert captured["url"].endswith("/works/10.5555%2F123")


def test_get_json_fails_fast_on_huge_retry_after():
    resp = MagicMock()
    resp.status_code = 429
    resp.headers = {"Retry-After": "66714"}
    resp.text = '{"error":"Rate limit exceeded"}'

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client.get.return_value = resp

    with patch("papers_library_pipeline.http_util.httpx.Client", return_value=mock_client):
        with pytest.raises(HttpRateLimited):
            get_json("https://api.openalex.org/works")


def test_crossref_get_by_doi_percent_encodes_slash():
    captured: dict = {}

    def fake_get_json(url, params=None, retries=4, user_agent=""):
        captured["url"] = url
        return {
            "message": {
                "DOI": "10.1038/nature14539",
                "title": ["Gene editing"],
                "author": [],
                "type": "journal-article",
                "created": {"date-parts": [[2015]]},
            }
        }

    with patch.object(crossref_client, "get_json", side_effect=fake_get_json):
        rec = crossref_client.get_by_doi("10.1038/nature14539")
    assert rec is not None
    assert "%2F" in captured["url"] or captured["url"].endswith("nature14539")
    # slash in DOI must not remain as a raw path segment separator alone
    assert "works/10.1038%2Fnature14539" in captured["url"]


def test_arxiv_pdf_url_from_doi():
    from papers_library_pipeline.pdf_fetch import arxiv_pdf_url_from_doi

    assert arxiv_pdf_url_from_doi("10.48550/arXiv.1706.03762") == (
        "https://arxiv.org/pdf/1706.03762.pdf"
    )
    assert arxiv_pdf_url_from_doi("10.1038/nature14539") is None


def test_openalex_marks_rate_limited_and_skips_further_calls(monkeypatch):
    openalex_client.reset_rate_limit_state()

    def boom(*_a, **_k):
        raise HttpRateLimited("429 budget gone")

    monkeypatch.setattr(openalex_client, "get_json", boom)
    assert openalex_client.search_works("q") == []
    assert openalex_client.is_rate_limited()
    # No further HTTP — returns empty/None immediately
    assert openalex_client.search_works("q2") == []
    assert openalex_client.search_by_doi("10.1/x") is None
    assert openalex_client.get_work_by_id("W1") is None
    openalex_client.reset_rate_limit_state()


def test_enrich_seed_falls_back_to_crossref_when_openalex_limited(monkeypatch):
    from papers_library_pipeline import run_harvest

    openalex_client.reset_rate_limit_state()
    openalex_client.mark_rate_limited("test budget")

    def fake_cr_doi(doi, mailto="x"):
        return {
            "source": "crossref",
            "doi": doi.lower(),
            "title": "From Crossref",
            "authors": ["A"],
            "year": 2020,
            "type": "article",
            "cited_by_count": 1,
            "abstract": "",
            "referenced_works": [],
            "isbn": None,
            "language": None,
        }

    monkeypatch.setattr(crossref_client, "get_by_doi", fake_cr_doi)
    cfg = {"mailto": "u@example.org", "include_keywords": [], "exclude_keywords": []}
    # No seed title → must come from Crossref after OpenAlex skip
    rec = run_harvest.enrich_seed({"doi": "10.1038/nature14539"}, cfg)
    assert rec["title"] == "From Crossref"
    assert "nature14539" in (rec.get("doi") or "")
    openalex_client.reset_rate_limit_state()
