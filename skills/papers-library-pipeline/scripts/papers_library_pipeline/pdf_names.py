"""PDF on-disk naming: `{local_id}.{title}.pdf` only."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Windows-forbidden + path separators; also drop control chars.
_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WS = re.compile(r"\s+")
_MULTI_US = re.compile(r"_+")
# Require id + name: "1001.Some_Title"
_STEM_ID_NAME = re.compile(r"^(\d+)\.(.+)$")

DEFAULT_TITLE_MAX = 80


def sanitize_title_for_filename(title: str | None, *, max_len: int = DEFAULT_TITLE_MAX) -> str:
    if not title:
        return ""
    s = _INVALID.sub("_", str(title).strip())
    s = _WS.sub("_", s)
    s = _MULTI_US.sub("_", s).strip("._ ")
    if len(s) > max_len:
        s = s[:max_len].rstrip("._ ")
    return s


def pdf_basename(local_id: Any, title: str | None = None, *, max_len: int = DEFAULT_TITLE_MAX) -> str:
    """Return `{id}.{name}.pdf`. Missing title → `{id}.untitled.pdf`."""
    lid = str(local_id).strip()
    name = sanitize_title_for_filename(title, max_len=max_len) or "untitled"
    return f"{lid}.{name}.pdf"


def parse_pdf_stem(stem: str) -> tuple[int | None, str]:
    """Parse `{id}.{name}` stem → (local_id, name). Bare `{id}` is invalid."""
    m = _STEM_ID_NAME.match(stem)
    if not m:
        return None, stem
    return int(m.group(1)), m.group(2)


def find_pdf_for_id(pdf_dir: Path | None, local_id: Any) -> Path | None:
    """Find `{id}.*.pdf` under pdf_dir (no bare `{id}.pdf`)."""
    if pdf_dir is None or local_id is None:
        return None
    pdf_dir = Path(pdf_dir)
    if not pdf_dir.is_dir():
        return None
    lid = str(local_id).strip()
    for p in sorted(pdf_dir.glob(f"{lid}.*.pdf")):
        if p.is_file() and parse_pdf_stem(p.stem)[0] is not None:
            return p
    return None
