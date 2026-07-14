"""Live network tests: OpenAlex, Crossref, and a real PDF download.

Requires outbound HTTPS. Optional: OPENALEX_API_KEY for higher OpenAlex quota.
Skip with: pytest -m "not network"
"""

from __future__ import annotations

from pathlib import Path

import pytest

from papers_library_pipeline import crossref_client, openalex_client
from papers_library_pipeline.pdf_fetch import download_paper_pdf, fetch_pdf_by_doi

pytestmark = pytest.mark.network

# arXiv DOI — present in OpenAlex; public PDF on arxiv.org
ARXIV_DOI = "10.48550/arXiv.1706.03762"
ARXIV_PDF = "https://arxiv.org/pdf/1706.03762.pdf"
# Classic journal DOI — registered in Crossref (arXiv DOIs often are not)
CROSSREF_DOI = "10.1038/nature14539"


def test_openalex_search_by_doi_live():
    openalex_client.reset_rate_limit_state()
    rec = openalex_client.search_by_doi(ARXIV_DOI)
    if openalex_client.is_rate_limited() or rec is None:
        pytest.skip(
            "OpenAlex rate/budget limited or empty; "
            "set OPENALEX_API_KEY or retry after UTC midnight reset."
        )
    assert rec.get("doi")
    assert "1706.03762" in (rec.get("doi") or "") or "attention" in (rec.get("title") or "").lower()
    assert rec.get("title")
    assert rec.get("source") == "openalex"


def test_openalex_search_works_live():
    openalex_client.reset_rate_limit_state()
    hits = openalex_client.search_works("attention is all you need", per_page=3)
    if openalex_client.is_rate_limited() or not hits:
        pytest.skip(
            "OpenAlex rate/budget limited or empty; "
            "set OPENALEX_API_KEY or retry after UTC midnight reset."
        )
    assert hits[0].get("title")


def test_crossref_get_by_doi_live():
    rec = crossref_client.get_by_doi(CROSSREF_DOI)
    assert rec is not None
    assert rec.get("doi")
    assert CROSSREF_DOI.lower() in (rec.get("doi") or "")
    assert rec.get("title")
    assert rec.get("source") == "crossref"


def test_crossref_search_works_live():
    hits = crossref_client.search_works("attention is all you need transformer", rows=3)
    assert isinstance(hits, list)
    assert len(hits) >= 1
    assert hits[0].get("title") or hits[0].get("doi")


def test_download_arxiv_pdf_direct_live(tmp_path: Path):
    out = tmp_path / "1706.03762.pdf"
    ok = download_paper_pdf(ARXIV_PDF, out)
    assert ok is True
    assert out.is_file()
    assert out.stat().st_size > 10_000
    assert out.read_bytes()[:5] == b"%PDF-"


def test_fetch_pdf_by_doi_live(tmp_path: Path):
    """Resolve arXiv DOI (OA/arXiv fallback) and download a real PDF."""
    out = tmp_path / "by-doi.pdf"
    result = fetch_pdf_by_doi(ARXIV_DOI, out)
    assert result.get("status") == "success", result
    assert result.get("downloaded") is True
    assert out.is_file()
    assert out.read_bytes()[:5] == b"%PDF-"
    assert out.stat().st_size > 10_000
