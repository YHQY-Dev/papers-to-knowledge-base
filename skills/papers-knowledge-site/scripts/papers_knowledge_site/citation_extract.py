"""Extract bibliographic clues from converted markdown."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\]\)|>\"']+", re.I)
REF_HEADER_RE = re.compile(
    r"(?im)^(#{1,3}\s*)?(references|bibliography|literature cited|参考文献|引用文献)\s*$"
)


def extract_from_markdown(text: str, source_id: int | str) -> dict[str, Any]:
    dois = sorted({m.group(0).rstrip(".,;") for m in DOI_RE.finditer(text)})
    lines = text.splitlines()
    ref_start = None
    for i, line in enumerate(lines):
        if REF_HEADER_RE.match(line.strip()):
            ref_start = i + 1
            break
    ref_lines: list[str] = []
    if ref_start is not None:
        for line in lines[ref_start:]:
            if re.match(r"(?i)^#{1,3}\s+\S+", line) and not REF_HEADER_RE.match(
                line.strip()
            ):
                break
            s = line.strip()
            if s:
                ref_lines.append(s)
    return {
        "source_id": source_id,
        "doi_mentions": dois,
        "reference_lines": ref_lines[:500],
        "reference_line_count": len(ref_lines),
    }


def extract_file(md_path: Path, source_id: int | str, out_path: Path) -> dict[str, Any]:
    text = md_path.read_text(encoding="utf-8", errors="replace")
    data = extract_from_markdown(text, source_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Extract DOIs/refs from markdown")
    ap.add_argument("md", type=Path)
    ap.add_argument("--id", required=True, help="source local id")
    ap.add_argument("-o", "--out", type=Path, required=True)
    args = ap.parse_args()
    data = extract_file(args.md, args.id, args.out)
    print(json.dumps({"dois": len(data["doi_mentions"]), "refs": data["reference_line_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
