"""Tests for string preservation (leading zeros, etc.)."""

from csvmedic.detectors.strings import detect_string_preservation


def test_leading_zeros_preserved() -> None:
    values = ["00742", "00123", "00456", "12345", "00001"]
    r = detect_string_preservation(values)
    assert r.should_preserve is True
    assert "leading_zeros" in r.reason.lower()


def test_no_leading_zeros() -> None:
    values = ["100", "200", "300"]
    r = detect_string_preservation(values)
    assert r.should_preserve is False
