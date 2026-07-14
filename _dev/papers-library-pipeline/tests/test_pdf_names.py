from pathlib import Path

from papers_library_pipeline.pdf_names import (
    find_pdf_for_id,
    parse_pdf_stem,
    pdf_basename,
    sanitize_title_for_filename,
)


def test_sanitize_title_strips_invalid_and_collapses():
    assert sanitize_title_for_filename('A/B: "C"?') == "A_B_C"
    assert sanitize_title_for_filename("  hello   world  ") == "hello_world"
    assert "\\" not in sanitize_title_for_filename("x\\y")


def test_pdf_basename_always_id_dot_name():
    assert pdf_basename(1001, "Small-Angle Scattering") == "1001.Small-Angle_Scattering.pdf"
    assert pdf_basename(7, None) == "7.untitled.pdf"
    assert pdf_basename(7, "   ") == "7.untitled.pdf"


def test_parse_pdf_stem_requires_name():
    assert parse_pdf_stem("1001.Some_Title") == (1001, "Some_Title")
    assert parse_pdf_stem("1001") == (None, "1001")
    assert parse_pdf_stem("not-an-id") == (None, "not-an-id")


def test_find_pdf_for_id_named_only(tmp_path: Path):
    pdf_dir = tmp_path
    named = pdf_dir / "1001.Hello_World.pdf"
    named.write_bytes(b"%PDF-1.4")
    assert find_pdf_for_id(pdf_dir, 1001) == named

    # bare id.pdf must NOT be resolved
    bare = pdf_dir / "1002.pdf"
    bare.write_bytes(b"%PDF-1.4")
    assert find_pdf_for_id(pdf_dir, 1002) is None

    assert find_pdf_for_id(pdf_dir, 9999) is None
