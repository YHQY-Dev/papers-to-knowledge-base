from pathlib import Path

from papers_library_pipeline.manifest import sync_from_disk
from papers_library_pipeline.paths import ensure_dirs, load_config, resolve_root


def test_resolve_root_defaults_to_cwd(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert resolve_root(None) == tmp_path.resolve()
    assert resolve_root(".") == tmp_path.resolve()
    assert resolve_root("") == tmp_path.resolve()
    assert resolve_root("./") == tmp_path.resolve()


def test_resolve_root_relative_against_cwd(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sub = tmp_path / "out"
    sub.mkdir()
    assert resolve_root("out") == sub.resolve()


def test_load_config_root_dot(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / "domain_config.json"
    cfg_path.write_text(
        '{"domain": "demo", "root": ".", "search_themes": []}',
        encoding="utf-8",
    )
    monkeypatch.setenv("DOMAIN_KB_CONFIG", str(cfg_path))
    cfg = load_config()
    assert cfg["_root"] == tmp_path.resolve()
    assert cfg["_pdf"] == tmp_path / "demo-pdf"


def test_ensure_dirs_does_not_create_md_or_web(tmp_path: Path):
    cfg = {
        "_pdf": tmp_path / "d-pdf",
        "_md": tmp_path / "d-md",
        "_catalog": tmp_path / "d-catalog",
        "_candidates_dir": tmp_path / "d-candidates",
        "_ai_reviews": tmp_path / "d-catalog" / "ai-reviews",
        "_citation_extracts": tmp_path / "d-catalog" / "citation-extracts",
        "_web": tmp_path / "d-web",
    }
    ensure_dirs(cfg)
    assert cfg["_pdf"].is_dir()
    assert cfg["_catalog"].is_dir()
    assert cfg["_candidates_dir"].is_dir()
    assert cfg["_ai_reviews"].is_dir()
    assert not cfg["_md"].exists()
    assert not cfg["_web"].exists()
    assert not cfg["_citation_extracts"].exists()


def test_sync_from_disk_pdf_only_without_md_dir(tmp_path: Path):
    pdf_dir = tmp_path / "pdf"
    pdf_dir.mkdir()
    (pdf_dir / "1001.T.pdf").write_bytes(b"%PDF-1.4")
    man_path = tmp_path / "manifest.json"
    man = sync_from_disk(
        man_path,
        pdf_dir,
        md_dir=None,
        candidates=[{"local_id": 1001, "title": "T", "doi": "10.1/x"}],
    )
    assert man_path.is_file()
    assert len(man["items"]) == 1
    assert man["items"][0]["pdf"] is True
    assert str(man["items"][0]["pdf_path"]).endswith("1001.T.pdf")
    assert man["items"][0].get("md") is False
