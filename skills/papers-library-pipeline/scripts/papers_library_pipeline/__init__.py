"""Literature harvest, PDF download, catalog, Excel export."""

from .candidates import is_accepted
from .export_excel import export_literature_excel
from .pdf_names import find_pdf_for_id, pdf_basename
from .pdf_fetch import (
    download_paper_pdf,
    fetch_pdf_by_doi,
    fetch_selected,
    get_paper_metadata,
    search_paper_by_doi,
    search_paper_by_title,
    search_papers_by_keyword,
)

__all__ = [
    "is_accepted",
    "pdf_basename",
    "find_pdf_for_id",
    "search_paper_by_doi",
    "search_paper_by_title",
    "search_papers_by_keyword",
    "get_paper_metadata",
    "download_paper_pdf",
    "fetch_pdf_by_doi",
    "fetch_selected",
    "export_literature_excel",
]
