"""Export literature triage table to .xlsx for humans."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import Workbook

from .candidates import _truthy_flag, is_accepted

EXCEL_COLUMNS = [
    "local_id",
    "title",
    "type",
    "doi",
    "isbn",
    "year",
    "script_score",
    "ai_score",
    "accepted",
    "decision",
    "reason",
    "pdf_status",
    "pdf_path",
    "notes",
]


def _accepted_cell(rec: dict[str, Any]) -> str:
    if is_accepted(rec):
        return "yes"
    for field in ("accepted", "selected"):
        if _truthy_flag(rec.get(field)) is False:
            return "no"
    return ""


def _derive_pdf_fields(
    rec: dict[str, Any], pdf_dir: Path | None
) -> tuple[str, str]:
    """Return (pdf_status, pdf_path), preferring explicit fields then disk."""
    from .pdf_names import find_pdf_for_id

    status = rec.get("pdf_status")
    path = rec.get("pdf_path")
    if status and path:
        return str(status), str(path)
    if pdf_dir is None:
        return ("" if status is None else str(status), "" if path is None else str(path))

    lid = rec.get("local_id")
    if lid is None:
        return (
            str(status) if status else "not_attempted",
            "" if path is None else str(path),
        )

    disk = find_pdf_for_id(pdf_dir, lid)
    if disk is not None and disk.is_file() and disk.stat().st_size > 0:
        try:
            head = disk.read_bytes()[:5]
            ok = head.startswith(b"%PDF")
        except OSError:
            ok = False
        if ok:
            return "downloaded", str(disk)
        return (str(status) if status else "failed", str(disk))

    if status:
        return str(status), "" if path is None else str(path)
    return "not_attempted", ""


def export_literature_excel(
    items: list[dict[str, Any]],
    path: Path,
    *,
    pdf_dir: Path | None = None,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "literature"
    ws.append(EXCEL_COLUMNS)
    for rec in items:
        pdf_status, pdf_path = _derive_pdf_fields(rec, pdf_dir)
        row = []
        for col in EXCEL_COLUMNS:
            if col == "accepted":
                row.append(_accepted_cell(rec))
            elif col == "pdf_status":
                row.append(pdf_status)
            elif col == "pdf_path":
                row.append(pdf_path)
            else:
                val = rec.get(col)
                row.append("" if val is None else val)
        ws.append(row)
    wb.save(path)
    return path


def main() -> int:
    import argparse

    from .candidates import load_candidates
    from .paths import load_config

    ap = argparse.ArgumentParser(description="Export literature.xlsx from candidates")
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("-o", "--out", type=Path, default=None)
    ap.add_argument(
        "--pdf-dir",
        type=Path,
        default=None,
        help="Derive pdf_status/pdf_path from this dir (default: config _pdf)",
    )
    args = ap.parse_args()
    cfg = load_config(args.config)
    items = load_candidates(cfg["_candidates"])
    out = args.out or (Path(cfg["_catalog"]) / "literature.xlsx")
    pdf_dir = args.pdf_dir if args.pdf_dir is not None else Path(cfg["_pdf"])
    export_literature_excel(items, out, pdf_dir=pdf_dir)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
