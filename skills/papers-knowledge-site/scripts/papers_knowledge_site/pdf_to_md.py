"""PDF → Markdown via MarkItDown (default) or text from optional PaddleOCR MCP."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _safe_stem(name: str) -> str:
    s = re.sub(r"[^\w.\-]+", "_", name, flags=re.U).strip("._")
    return s[:120] or "content"


def _bundle_dirname_for_pdf(pdf: Path) -> str:
    """Prefer numeric local_id prefix from `{id}.{title}.pdf`; else full stem."""
    m = re.match(r"^(\d+)", pdf.stem)
    return m.group(1) if m else pdf.stem


def write_md_bundle(
    pdf_path: Path,
    out_dir: Path,
    text: str,
    *,
    md_name: str | None = None,
    extract_images: bool = True,
    converter: str = "markitdown",
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Write the standard {DOMAIN}-md/{id}/ bundle from already-obtained text.

    Use after PaddleOCR MCP `paddleocr_vl`, or internally from MarkItDown.
    """
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = md_name or "content"
    md_path = out_dir / f"{_safe_stem(stem)}.md"
    md_path.write_text(text or "", encoding="utf-8")

    meta: dict[str, Any] = {
        "pdf": str(pdf_path.resolve()) if pdf_path.exists() else str(pdf_path),
        "markdown": str(md_path.resolve()),
        "chars": len(text or ""),
        "converter": converter,
    }
    if extra_meta:
        meta.update(extra_meta)

    if extract_images and pdf_path.is_file():
        from .extract_pdf_images import extract_images as _extract

        imgs = _extract(pdf_path, out_dir / "imgs")
        meta["image_count"] = len(imgs)
        meta["images"] = imgs
        (out_dir / "images_meta.json").write_text(
            json.dumps(
                {"pdf": str(pdf_path), "image_count": len(imgs), "images": imgs},
                indent=2,
            ),
            encoding="utf-8",
        )

    (out_dir / "convert_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta


def convert_pdf(
    pdf_path: Path,
    out_dir: Path,
    *,
    md_name: str | None = None,
    extract_images: bool = True,
    enable_plugins: bool = False,
) -> dict[str, Any]:
    """Convert one PDF with MarkItDown (default path; no OCR)."""
    from markitdown import MarkItDown

    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    md = MarkItDown(enable_plugins=enable_plugins)
    result = md.convert(str(pdf_path))
    text = result.text_content or ""
    return write_md_bundle(
        pdf_path,
        out_dir,
        text,
        md_name=md_name,
        extract_images=extract_images,
        converter="markitdown",
        extra_meta={"enable_plugins": enable_plugins},
    )


def convert_batch(
    pdf_dir: Path,
    md_root: Path,
    *,
    extract_images: bool = True,
    enable_plugins: bool = False,
) -> list[dict[str, Any]]:
    """Convert every *.pdf in pdf_dir into md_root/{local_id}/."""
    pdf_dir = Path(pdf_dir)
    md_root = Path(md_root)
    results: list[dict[str, Any]] = []
    for pdf in sorted(pdf_dir.glob("*.pdf")):
        out_dir = md_root / _bundle_dirname_for_pdf(pdf)
        existing_md = out_dir / "content.md"
        if existing_md.exists() and existing_md.stat().st_size > 200:
            results.append(
                {
                    "pdf": str(pdf),
                    "markdown": str(existing_md),
                    "chars": existing_md.stat().st_size,
                    "status": "already_present",
                }
            )
            continue
        try:
            results.append(
                convert_pdf(
                    pdf,
                    out_dir,
                    extract_images=extract_images,
                    enable_plugins=enable_plugins,
                )
            )
        except Exception as exc:
            results.append(
                {"pdf": str(pdf), "status": "error", "error": f"{type(exc).__name__}: {exc}"}
            )
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="PDF → Markdown with MarkItDown")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("convert", help="Convert one PDF")
    p.add_argument("pdf", type=Path)
    p.add_argument("--out-dir", type=Path, required=True, help="{DOMAIN}-md/{id}")
    p.add_argument("--name", default="content", help="Markdown basename (default content)")
    p.add_argument("--no-images", action="store_true", help="Skip PyMuPDF image extract")
    p.add_argument("--plugins", action="store_true", help="enable_plugins=True")

    p = sub.add_parser("batch", help="Convert all PDFs in a directory")
    p.add_argument("--pdf-dir", type=Path, required=True)
    p.add_argument("--md-dir", type=Path, required=True, help="{DOMAIN}-md root")
    p.add_argument("--no-images", action="store_true")
    p.add_argument("--plugins", action="store_true")

    args = ap.parse_args(argv)

    if args.cmd == "convert":
        meta = convert_pdf(
            args.pdf,
            args.out_dir,
            md_name=args.name,
            extract_images=not args.no_images,
            enable_plugins=args.plugins,
        )
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        return 0 if meta.get("chars", 0) > 0 else 1

    results = convert_batch(
        args.pdf_dir,
        args.md_dir,
        extract_images=not args.no_images,
        enable_plugins=args.plugins,
    )
    ok = sum(
        1
        for r in results
        if r.get("chars", 0) > 0 or r.get("status") == "already_present"
    )
    print(json.dumps({"ok": ok, "total": len(results), "results": results}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
