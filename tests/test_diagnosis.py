"""Tests for Diagnosis and FileProfile serialization."""

from pathlib import Path

import pytest

import csvmedic
from csvmedic.models import DetectedType

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_diagnosis_repr() -> None:
    path = FIXTURES_DIR / "us_standard.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    df = csvmedic.read(path)
    repr_str = repr(df.diagnosis)
    assert "csvmedic Diagnosis" in repr_str
    assert "Encoding:" in repr_str
    assert "Delimiter:" in repr_str
    assert "Shape:" in repr_str


def test_diagnosis_columns_access() -> None:
    path = FIXTURES_DIR / "us_standard.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    df = csvmedic.read(path)
    cols = df.diagnosis.columns
    assert "id" in cols
    assert cols["id"].detected_type in (DetectedType.STRING, DetectedType.INTEGER)
    assert cols["id"].confidence >= 0


def test_file_profile_to_dict() -> None:
    path = FIXTURES_DIR / "us_standard.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    profile = csvmedic.read_raw(path)
    d = profile.to_dict()
    assert "encoding_detected" in d
    assert "delimiter_detected" in d
    assert "columns" in d
    assert "row_count" in d
    assert "column_count" in d


def test_file_profile_summary() -> None:
    path = FIXTURES_DIR / "us_standard.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    profile = csvmedic.read_raw(path)
    s = profile.summary()
    assert "FileProfile" in s
    assert "encoding" in s.lower() or "delimiter" in s.lower()
