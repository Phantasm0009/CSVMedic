"""Tests for encoding detection."""

from pathlib import Path

import pytest

from csvmedic.detectors.encoding import EncodingResult, detect_encoding
from csvmedic.exceptions import EncodingDetectionError


def test_utf8_detected(tmp_path: Path) -> None:
    content = "a,b,c\n1,2,3\n"
    (tmp_path / "f.csv").write_text(content, encoding="utf-8")
    result = detect_encoding(tmp_path / "f.csv")
    assert result.encoding.lower() in ("utf-8", "utf_8")
    assert result.confidence >= 0.5


def test_utf8_bom_detected(tmp_path: Path) -> None:
    path = tmp_path / "f.csv"
    path.write_bytes(b"\xef\xbb\xbf" + b"a,b,c\n1,2,3\n")
    result = detect_encoding(path)
    assert "utf-8" in result.encoding.lower() or "utf_8" in result.encoding.lower()
    assert result.confidence >= 0.9


def test_windows1252_detected(tmp_path: Path) -> None:
    content = "Müller;Schäfer;Böhm\n"
    (tmp_path / "f.csv").write_text(content, encoding="cp1252")
    result = detect_encoding(tmp_path / "f.csv")
    # charset-normalizer may return cp1252, cp1250, or mac_latin2 for Latin-1–like content
    assert any(
        x in result.encoding.lower()
        for x in ("1252", "1250", "windows-1252", "cp1252", "mac_latin", "latin")
    )
    assert result.confidence >= 0.5


def test_empty_file_returns_utf8(tmp_path: Path) -> None:
    (tmp_path / "empty.csv").write_bytes(b"")
    result = detect_encoding(tmp_path / "empty.csv")
    assert result.encoding == "utf-8"
    assert result.confidence == 0.0


def test_encoding_result_attributes() -> None:
    r = EncodingResult(encoding="utf-8", confidence=0.9)
    assert r.encoding == "utf-8"
    assert r.confidence == 0.9


def test_file_not_found_raises() -> None:
    with pytest.raises(EncodingDetectionError):
        detect_encoding("/nonexistent/path/file.csv")


def test_buffer_bytes_detection() -> None:
    result = detect_encoding(b"hello,world\n1,2\n")
    assert result.encoding
    assert 0 <= result.confidence <= 1.0
