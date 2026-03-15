"""Tests for boolean detection."""

from csvmedic.detectors.booleans import detect_boolean_column


def test_yes_no_english() -> None:
    values = ["Yes", "No", "Yes", "No", "Yes"]
    r = detect_boolean_column(values)
    assert r.is_boolean is True
    assert r.confidence >= 0.9


def test_ja_nein_german() -> None:
    values = ["Ja", "Nein", "Ja", "Nein"]
    r = detect_boolean_column(values)
    assert r.is_boolean is True
    assert "ja" in [v.lower() for v in r.true_variants]
    assert "nein" in [v.lower() for v in r.false_variants]


def test_oui_non_french() -> None:
    values = ["Oui", "Non", "Oui", "Non"]
    r = detect_boolean_column(values)
    assert r.is_boolean is True


def test_more_than_two_values_not_boolean() -> None:
    values = ["A", "B", "C", "D"]
    r = detect_boolean_column(values)
    assert r.is_boolean is False


def test_mixed_case() -> None:
    values = ["YES", "no", "Yes", "NO"]
    r = detect_boolean_column(values)
    assert r.is_boolean is True
