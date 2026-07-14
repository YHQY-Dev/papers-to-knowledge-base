"""PDF search + download (httpx). Prefer calling these functions; no MCP required."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .http_util import get_json

logger = logging.getLogger(__name__)

PAPER_SOURCES = [
    "https://sci-hub.al",
    "https://sci-hub.mk",
    "https://sci-hub.ee",
    "https://sci-hub.vg",
    "https://sci-hub.st",
    "https://sci-hub.ru",
    "https://sci-hub.box",
    "https://sci-hub.red",
]

DEFAULT_TIMEOUT = httpx.Timeout(20.0, connect=8.0)
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _client(*, verify: bool = False) -> httpx.Client:
    return httpx.Client(
        timeout=DEFAULT_TIMEOUT,
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        verify=verify,
    )


def _normalize_doi(doi: str) -> str:
    doi = doi.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.I)
    return doi.strip("/")


def _absolute_url(base: str, href: str) -> str:
    href = href.strip().strip("'\"")
    if href.startswith("//"):
        return "https:" + href
    return urljoin(base if base.endswith("/") else base + "/", href)


def _extract_pdf_url(html: str, page_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    for tag_name, attr in (("embed", "src"), ("iframe", "src"), ("object", "data")):
        for tag in soup.find_all(tag_name):
            src = tag.get(attr)
            if src and (".pdf" in src.lower() or "pdf" in src.lower()):
                return _absolute_url(page_url, src)

    pdf_btn = soup.select_one("#pdf, button#pdf, a#pdf")
    if pdf_btn:
        for attr in ("onclick", "href", "data-src", "src"):
            val = pdf_btn.get(attr)
            if not val:
                continue
            m = re.search(
                r"(https?://[^\s'\"]+\.pdf[^\s'\"]*|//[^\s'\"]+\.pdf[^\s'\"]*)",
                val,
                re.I,
            )
            if m:
                return _absolute_url(page_url, m.group(1))
            if ".pdf" in val or val.startswith("/") or val.startswith("http"):
                return _absolute_url(page_url, val)

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower():
            return _absolute_url(page_url, href)

    for pattern in (
        r'(?:src|href)\s*=\s*[\'"]([^\'"]+\.pdf[^\'"]*)[\'"]',
        r'location\.href\s*=\s*[\'"]([^\'"]+\.pdf[^\'"]*)[\'"]',
        r'(//[a-zA-Z0-9._/-]+\.pdf(?:\?[^\s\'"]*)?)',
    ):
        m = re.search(pattern, html, re.I)
        if m:
            return _absolute_url(page_url, m.group(1))

    return None


def _fetch_crossref_metadata(doi: str) -> dict[str, Any]:
    doi = _normalize_doi(doi)
    url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
    try:
        with _client(verify=True) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return {}
            msg = resp.json().get("message", {})
            authors = []
            for a in msg.get("author", []) or []:
                name = " ".join(x for x in [a.get("given"), a.get("family")] if x)
                if name:
                    authors.append(name)
            year = None
            for key in ("published-print", "published-online", "created"):
                parts = (msg.get(key) or {}).get("date-parts") or []
                if parts and parts[0]:
                    year = parts[0][0]
                    break
            titles = msg.get("title") or []
            return {
                "title": titles[0] if titles else "",
                "author": ", ".join(authors),
                "year": year or "",
                "container": (msg.get("container-title") or [""])[0],
            }
    except Exception as exc:
        logger.warning("CrossRef metadata failed: %s", exc)
        return {}


def arxiv_pdf_url_from_doi(doi: str) -> str | None:
    """Map arXiv DOIs (10.48550/arXiv.*) to the public arXiv PDF URL."""
    doi = _normalize_doi(doi).lower()
    m = re.search(r"10\.48550/arxiv\.(\d{4}\.\d{4,5})(v\d+)?", doi)
    if not m:
        m = re.search(r"(?:arxiv[:/]|arxiv\.)(\d{4}\.\d{4,5})(v\d+)?", doi)
    if not m:
        return None
    arxiv_id = m.group(1) + (m.group(2) or "")
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"


def resolve_oa_pdf_url(doi: str, mailto: str = "kb-harvester@example.com") -> str | None:
    """Unpaywall then OpenAlex OA URL, then arXiv DOI → PDF."""
    from . import openalex_client
    from .http_util import HttpRateLimited
    from .openalex_client import _auth_params, _user_agent

    doi = _normalize_doi(doi).lower()
    # Unpaywall rejects example.com / placeholder emails
    if mailto and not mailto.lower().endswith("@example.com"):
        try:
            data = get_json(f"https://api.unpaywall.org/v2/{doi}", {"email": mailto})
            loc = data.get("best_oa_location") or {}
            url = loc.get("url_for_pdf") or loc.get("url")
            if url:
                return url
        except Exception:
            pass
    if not openalex_client.is_rate_limited():
        try:
            data = get_json(
                "https://api.openalex.org/works",
                {"filter": f"doi:{doi}", **_auth_params(mailto)},
                user_agent=_user_agent(mailto),
            )
            results = data.get("results") or []
            if results:
                oa_url = (results[0].get("open_access") or {}).get("oa_url")
                if oa_url:
                    return oa_url
        except HttpRateLimited as e:
            openalex_client.mark_rate_limited(e)
        except Exception:
            pass
    return arxiv_pdf_url_from_doi(doi)


def search_paper_by_doi(doi: str) -> dict[str, Any]:
    """Find a PDF URL for a DOI (OA first, then mirror sources)."""
    doi = _normalize_doi(doi)
    meta = _fetch_crossref_metadata(doi)
    base = {
        "doi": doi,
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "year": meta.get("year", ""),
    }

    oa = resolve_oa_pdf_url(doi)
    if oa:
        source = "arxiv" if "arxiv.org/pdf/" in oa else "oa"
        return {**base, "pdf_url": oa, "status": "success", "source": source}

    errors: list[str] = []
    with _client() as client:
        for i, source in enumerate(PAPER_SOURCES, start=1):
            page_url = f"{source.rstrip('/')}/{doi}"
            try:
                resp = client.get(page_url)
                if resp.status_code >= 400:
                    errors.append(f"source#{i}: HTTP {resp.status_code}")
                    continue
                content_type = (resp.headers.get("content-type") or "").lower()
                if "pdf" in content_type or resp.content[:4] == b"%PDF":
                    return {
                        **base,
                        "pdf_url": str(resp.url),
                        "status": "success",
                        "source": f"mirror#{i}",
                    }
                pdf_url = _extract_pdf_url(resp.text, str(resp.url))
                if pdf_url:
                    return {
                        **base,
                        "pdf_url": pdf_url,
                        "status": "success",
                        "source": f"mirror#{i}",
                    }
                errors.append(f"source#{i}: no PDF on page")
            except Exception as exc:
                errors.append(f"source#{i}: {type(exc).__name__}")
                logger.warning("Literature source #%s failed: %s", i, type(exc).__name__)

    return {
        **base,
        "status": "not_found",
        "error": "; ".join(errors[-5:]) if errors else "No working sources",
    }


def search_paper_by_title(title: str) -> dict[str, Any]:
    try:
        with _client(verify=True) as client:
            resp = client.get(
                "https://api.crossref.org/works",
                params={"query.title": title, "rows": 1},
            )
            if resp.status_code == 200:
                items = resp.json().get("message", {}).get("items") or []
                if items and items[0].get("DOI"):
                    result = search_paper_by_doi(items[0]["DOI"])
                    result.setdefault("queried_title", title)
                    return result
    except Exception as exc:
        logger.warning("Title search failed: %s", exc)
    return {"title": title, "status": "not_found"}


def search_papers_by_keyword(keyword: str, num_results: int = 10) -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []
    try:
        with _client(verify=True) as client:
            resp = client.get(
                "https://api.crossref.org/works",
                params={"query": keyword, "rows": num_results},
            )
            if resp.status_code != 200:
                return papers
            for item in resp.json().get("message", {}).get("items") or []:
                doi = item.get("DOI")
                if not doi:
                    continue
                result = search_paper_by_doi(doi)
                if result.get("status") == "success":
                    papers.append(result)
    except Exception as exc:
        logger.warning("Keyword search failed: %s", exc)
    return papers


def get_paper_metadata(doi: str) -> dict[str, Any]:
    info = search_paper_by_doi(doi)
    if info.get("status") == "success":
        return {
            "doi": _normalize_doi(doi),
            "title": info.get("title", ""),
            "author": info.get("author", ""),
            "year": info.get("year", ""),
            "pdf_url": info.get("pdf_url", ""),
            "status": "success",
            "source": info.get("source"),
        }
    return {
        "doi": _normalize_doi(doi),
        "status": "not_found",
        "error": info.get("error") or f"未找到 DOI 为 {doi} 的文献",
    }


def _looks_like_pdf(path: Path) -> bool:
    try:
        if not path.exists() or path.stat().st_size < 1000:
            return False
        with path.open("rb") as f:
            return f.read(5).startswith(b"%PDF")
    except OSError:
        return False


def download_paper_pdf(pdf_url: str, output_path: str | Path) -> bool:
    """Download PDF. `pdf_url` may be a direct URL or a DOI."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf_url = pdf_url.strip()

    if not pdf_url.lower().endswith(".pdf") and "sci-hub" not in urlparse(pdf_url).netloc:
        if re.match(r"^10\.\d{4,9}/", pdf_url) or pdf_url.lower().startswith("10."):
            found = search_paper_by_doi(pdf_url)
            if found.get("status") != "success":
                return False
            pdf_url = found["pdf_url"]

    with _client() as client:
        try:
            with client.stream("GET", pdf_url) as resp:
                if resp.status_code >= 400:
                    html = client.get(pdf_url)
                    nested = _extract_pdf_url(html.text, str(html.url))
                    if not nested:
                        return False
                    with client.stream("GET", nested) as nested_resp:
                        nested_resp.raise_for_status()
                        with output.open("wb") as f:
                            for chunk in nested_resp.iter_bytes():
                                f.write(chunk)
                else:
                    resp.raise_for_status()
                    with output.open("wb") as f:
                        for chunk in resp.iter_bytes():
                            f.write(chunk)
            if _looks_like_pdf(output):
                return True
            if output.exists():
                output.unlink(missing_ok=True)
            return False
        except Exception as exc:
            logger.warning("Download failed: %s", exc)
            if output.exists():
                output.unlink(missing_ok=True)
            return False


def fetch_pdf_by_doi(doi: str, output_path: str | Path) -> dict[str, Any]:
    """One-shot: resolve DOI → download → return status dict."""
    found = search_paper_by_doi(doi)
    if found.get("status") != "success":
        return found
    ok = download_paper_pdf(found["pdf_url"], output_path)
    return {
        **found,
        "output_path": str(output_path),
        "downloaded": ok,
        "status": "success" if ok else "download_failed",
    }


def append_manual_needed(path: Path, doi: str | None, title: str | None, reason: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f"- doi={doi or '-'} | title={title or '-'} | {reason}\n"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in existing:
        return
    if not existing:
        existing = "# Manual download needed\n\n"
    path.write_text(existing + line, encoding="utf-8")


def fetch_selected(
    items: list[dict[str, Any]],
    pdf_dir: Path,
    manual_needed: Path | None = None,
    id_field: str = "local_id",
) -> list[dict[str, Any]]:
    """Download PDFs for records that have doi (+ local_id preferred).

    On-disk name: `{local_id}.{title}.pdf` (see `pdf_names.pdf_basename`).
    """
    from .pdf_names import find_pdf_for_id, pdf_basename

    pdf_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for rec in items:
        doi = rec.get("doi")
        if not doi:
            results.append({**rec, "status": "skipped_no_doi"})
            continue
        lid = rec.get(id_field)
        if lid is not None:
            existing = find_pdf_for_id(pdf_dir, lid)
            if existing is not None and _looks_like_pdf(existing):
                results.append(
                    {**rec, "status": "already_present", "output_path": str(existing)}
                )
                continue
            out = pdf_dir / pdf_basename(lid, rec.get("title"))
        else:
            out = pdf_dir / f"{_normalize_doi(doi).replace('/', '_')}.pdf"
            if _looks_like_pdf(out):
                results.append({**rec, "status": "already_present", "output_path": str(out)})
                continue
        got = fetch_pdf_by_doi(doi, out)
        results.append({**rec, **got})
        if got.get("status") != "success" and manual_needed is not None:
            append_manual_needed(
                manual_needed,
                doi,
                rec.get("title") or got.get("title"),
                got.get("error") or got.get("status") or "download_failed",
            )
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Literature PDF search/download")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("search-doi", help="Resolve PDF URL by DOI")
    p.add_argument("doi")

    p = sub.add_parser("search-title", help="Resolve PDF URL by title")
    p.add_argument("title")

    p = sub.add_parser("search-keyword", help="Search papers by keyword")
    p.add_argument("keyword")
    p.add_argument("-n", "--num-results", type=int, default=10)

    p = sub.add_parser("metadata", help="Metadata + pdf_url for DOI")
    p.add_argument("doi")

    p = sub.add_parser("download", help="Download PDF (DOI or URL)")
    p.add_argument("pdf_url")
    p.add_argument("-o", "--out", required=True, type=Path)

    p = sub.add_parser("fetch", help="Resolve DOI and download in one step")
    p.add_argument("doi")
    p.add_argument("-o", "--out", required=True, type=Path)

    p = sub.add_parser("fetch-batch", help="Download from candidates JSON (items with doi)")
    p.add_argument("candidates", type=Path, help="candidates.json or a JSON list")
    p.add_argument("--pdf-dir", type=Path, required=True)
    p.add_argument("--manual", type=Path, default=None, help="manual-needed.md path")
    p.add_argument(
        "--selected-only",
        action="store_true",
        help="Only items with accepted=yes/true or selected=true (aliases)",
    )
    p.add_argument(
        "--assign-ids",
        action="store_true",
        help="Assign missing local_id (uses candidates.json next_id)",
    )
    p.add_argument("--next-id", type=int, default=None, help="Override next_id when assigning")

    args = ap.parse_args(argv)

    if args.cmd == "search-doi":
        print(json.dumps(search_paper_by_doi(args.doi), ensure_ascii=False, indent=2))
    elif args.cmd == "search-title":
        print(json.dumps(search_paper_by_title(args.title), ensure_ascii=False, indent=2))
    elif args.cmd == "search-keyword":
        print(
            json.dumps(
                search_papers_by_keyword(args.keyword, args.num_results),
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.cmd == "metadata":
        print(json.dumps(get_paper_metadata(args.doi), ensure_ascii=False, indent=2))
    elif args.cmd == "download":
        ok = download_paper_pdf(args.pdf_url, args.out)
        print(args.out if ok else "download failed", file=sys.stdout if ok else sys.stderr)
        return 0 if ok else 1
    elif args.cmd == "fetch":
        result = fetch_pdf_by_doi(args.doi, args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("downloaded") else 1
    elif args.cmd == "fetch-batch":
        from .candidates import (
            assign_local_ids,
            is_accepted,
            load_candidates_doc,
            save_candidates,
        )

        doc = load_candidates_doc(args.candidates)
        items = list(doc["items"])
        next_id = args.next_id if args.next_id is not None else int(doc.get("next_id") or 1000)
        if args.assign_ids:
            items, next_id = assign_local_ids(
                items, next_id, only_selected=args.selected_only
            )
            save_candidates(args.candidates, items, next_id=next_id)
        work = [x for x in items if is_accepted(x)] if args.selected_only else items
        results = fetch_selected(work, args.pdf_dir, args.manual)
        ok_n = sum(1 for r in results if r.get("status") in {"success", "already_present"})
        print(
            json.dumps(
                {"ok": ok_n, "total": len(results), "next_id": next_id, "results": results},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if ok_n else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
