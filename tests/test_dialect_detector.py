"""Tests for dialect detection."""

from pathlib import Path

from csvmedic.detectors.dialect import DialectResult, detect_dialect


def test_comma_delimiter(tmp_path: Path) -> None:
    (tmp_path / "f.csv").write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    result = detect_dialect(tmp_path / "f.csv", "utf-8")
    assert result.delimiter == ","
    assert result.has_header is True


def test_semicolon_delimiter(tmp_path: Path) -> None:
    (tmp_path / "f.csv").write_text("a;b;c\n1;2;3\n", encoding="utf-8")
    result = detect_dialect(tmp_path / "f.csv", "utf-8")
    assert result.delimiter == ";"


def test_tab_delimiter(tmp_path: Path) -> None:
    (tmp_path / "f.tsv").write_text("a\tb\tc\n1\t2\t3\n", encoding="utf-8")
    result = detect_dialect(tmp_path / "f.tsv", "utf-8")
    assert result.delimiter == "\t"


def test_pipe_delimiter(tmp_path: Path) -> None:
    (tmp_path / "f.csv").write_text("a|b|c\n1|2|3\n", encoding="utf-8")
    result = detect_dialect(tmp_path / "f.csv", "utf-8")
    assert result.delimiter == "|"


def test_quoted_field_with_comma(tmp_path: Path) -> None:
    (tmp_path / "f.csv").write_text('a,b,c\n1,"two, half",3\n', encoding="utf-8")
    result = detect_dialect(tmp_path / "f.csv", "utf-8")
    assert result.delimiter == ","
    assert result.quotechar == '"'


def test_dialect_result_attributes() -> None:
    r = DialectResult(delimiter=";", quotechar='"', has_header=True)
    assert r.delimiter == ";"
    assert r.quotechar == '"'
    assert r.has_header is True


def test_empty_file_default_dialect(tmp_path: Path) -> None:
    (tmp_path / "empty.csv").write_text("", encoding="utf-8")
    result = detect_dialect(tmp_path / "empty.csv", "utf-8")
    assert result.delimiter == ","
    assert result.has_header is True
