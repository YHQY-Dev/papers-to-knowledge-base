#!/usr/bin/env python3
"""Extract embedded images from PDFs into {id}/imgs/. Requires: pip install PyMuPDF"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def extract_images(pdf_path: Path, out_imgs: Path, min_size: int = 80) -> list[str]:
    import fitz  # PyMuPDF

    out_imgs.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    saved: list[str] = []
    for page_index in range(len(doc)):
        page = doc[page_index]
        for img_i, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
            except Exception:
                continue
            try:
                if pix.n - pix.alpha >= 4 or (
                    pix.colorspace is not None and pix.colorspace.n not in (1, 3)
                ):
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                if pix.alpha:
                    pix = fitz.Pixmap(pix, 0)
                if pix.n not in (1, 3):
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                    if pix.alpha:
                        pix = fitz.Pixmap(pix, 0)
            except Exception:
                continue
            if pix.width < min_size or pix.height < min_size:
                continue
            fname = f"page{page_index + 1:03d}_img{img_i:02d}.png"
            fpath = out_imgs / fname
            try:
                pix.save(fpath)
            except Exception:
                continue
            saved.append(fname)
    doc.close()
    return saved


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True, help="{DOMAIN}-md/{id} directory")
    args = ap.parse_args()
    imgs_dir = args.out_dir / "imgs"
    names = extract_images(args.pdf, imgs_dir)
    meta = {"pdf": str(args.pdf), "image_count": len(names), "images": names}
    (args.out_dir / "images_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print(json.dumps(meta, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
