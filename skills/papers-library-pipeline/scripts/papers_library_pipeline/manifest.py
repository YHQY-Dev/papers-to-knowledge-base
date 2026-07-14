from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .pdf_names import parse_pdf_stem


def load_manifest(path: Path, next_id_start: int = 1000) -> dict[str, Any]:
    if not path.exists():
        return {"next_id": next_id_start, "items": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_item(manifest: dict[str, Any], item: dict[str, Any]) -> None:
    items = manifest.setdefault("items", [])
    key = None
    if item.get("doi"):
        key = ("doi", item["doi"].lower())
    elif item.get("local_id") is not None:
        key = ("id", item["local_id"])
    elif item.get("title"):
        key = ("title", item["title"].lower())

    for i, existing in enumerate(items):
        match = False
        if key and key[0] == "doi" and (existing.get("doi") or "").lower() == key[1]:
            match = True
        elif key and key[0] == "id" and existing.get("local_id") == key[1]:
            match = True
        elif key and key[0] == "title" and (existing.get("title") or "").lower() == key[1]:
            match = True
        if match:
            items[i] = {**existing, **item}
            return
    items.append(item)


def allocate_id(manifest: dict[str, Any], next_id_start: int = 1000) -> int:
    nid = int(manifest.get("next_id") or next_id_start)
    manifest["next_id"] = nid + 1
    return nid


def sync_from_disk(
    manifest_path: Path,
    pdf_dir: Path,
    md_dir: Path | None = None,
    candidates: list[dict[str, Any]] | None = None,
    next_id_start: int = 1000,
) -> dict[str, Any]:
    """Upsert manifest rows from on-disk PDF (and optional MD); merge candidates metadata.

    PDF names: `{local_id}.{title}.pdf` only.
    """
    by_id: dict[Any, dict[str, Any]] = {}
    for rec in candidates or []:
        lid = rec.get("local_id")
        if lid is not None:
            by_id[lid] = rec

    man = load_manifest(manifest_path, next_id_start=next_id_start)
    pdf_dir = Path(pdf_dir)
    md_path_root = Path(md_dir) if md_dir is not None else None

    pdf_by_id: dict[Any, Path] = {}
    if pdf_dir.is_dir():
        for p in sorted(pdf_dir.glob("*.pdf")):
            lid, _name = parse_pdf_stem(p.stem)
            if lid is None:
                continue
            pdf_by_id[lid] = p

    md_ids: set[Any] = set()
    if md_path_root is not None and md_path_root.is_dir():
        for p in md_path_root.iterdir():
            if not p.is_dir():
                continue
            lid, _ = parse_pdf_stem(p.name)
            md_ids.add(lid if lid is not None else p.name)

    all_ids: set[Any] = set(pdf_by_id) | set(md_ids)

    for lid in sorted(all_ids, key=lambda x: (isinstance(x, str), x)):
        pdf_path = pdf_by_id.get(lid)
        md_file: Path | None = None
        imgs_dir: Path | None = None
        if md_path_root is not None and md_path_root.is_dir():
            # Prefer `{id}/` then `{id}.{name}/` folders
            candidates_dirs = []
            bare = md_path_root / str(lid)
            if bare.is_dir():
                candidates_dirs.append(bare)
            for d in sorted(md_path_root.glob(f"{lid}.*")):
                if d.is_dir():
                    candidates_dirs.append(d)
            for folder in candidates_dirs:
                content = folder / "content.md"
                if content.exists():
                    md_file = content
                    imgs_dir = folder / "imgs"
                    break
                md_files = list(folder.glob("*.md"))
                if md_files:
                    md_file = md_files[0]
                    imgs_dir = folder / "imgs"
                    break
        meta = by_id.get(lid) or {}
        item = {
            "local_id": lid,
            "doi": meta.get("doi"),
            "title": meta.get("title"),
            "pdf": pdf_path is not None and pdf_path.exists(),
            "pdf_path": str(pdf_path) if pdf_path and pdf_path.exists() else None,
            "md": bool(md_file and md_file.exists()),
            "md_path": str(md_file) if md_file and md_file.exists() else None,
            "images": bool(
                imgs_dir and imgs_dir.is_dir() and any(imgs_dir.iterdir())
            ),
        }
        upsert_item(man, item)

    save_manifest(manifest_path, man)
    return man
