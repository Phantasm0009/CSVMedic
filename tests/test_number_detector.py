"""Tests for number locale detection."""

from csvmedic.detectors.numbers import (
    _classify_separators,
    detect_number_column,
)


def test_us_number_format() -> None:
    values = ["1,234.56", "789.00", "12,345.67"]
    r = detect_number_column(values)
    assert r.is_numeric is True
    assert r.decimal_separator == "."
    assert r.thousands_separator == ","
    assert r.locale_hint == "en_US"


def test_european_number_format() -> None:
    values = ["1.234,56", "789,00", "12.345,67"]
    r = detect_number_column(values)
    assert r.is_numeric is True
    assert r.decimal_separator == ","
    assert r.thousands_separator == "."


def test_integer_plain() -> None:
    values = ["100", "200", "300"]
    r = detect_number_column(values)
    assert r.is_numeric is True
    assert r.is_integer is True


def test_leading_zeros_preserved() -> None:
    values = ["00742", "00123", "00456"]
    r = detect_number_column(values)
    assert r.has_leading_zeros is True
    assert r.is_numeric is True


def test_classify_us_both() -> None:
    dec, thou = _classify_separators("1,234.56")
    assert dec == "."
    assert thou == ","


def test_classify_eu_both() -> None:
    dec, thou = _classify_separators("1.234,56")
    assert dec == ","
    assert thou == "."
