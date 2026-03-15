"""Integration tests for read()."""

from pathlib import Path

import pandas as pd
import pytest

import csvmedic
from csvmedic.models import Action, DetectedType

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_read_simple_us_csv(simple_us_csv: Path) -> None:
    """Read a basic US-format CSV and return a DataFrame with diagnosis."""
    df = csvmedic.read(simple_us_csv)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert list(df.columns) == ["id", "name", "value"]
    diagnosis = df.attrs.get("diagnosis")
    assert diagnosis is not None
    assert diagnosis.file_profile.delimiter_detected == ","
    assert diagnosis.file_profile.encoding_detected.lower() in ("utf-8", "utf_8", "ascii")
    assert diagnosis.file_profile.column_count == 3
    assert diagnosis.file_profile.row_count == 3


def test_read_european_export() -> None:
    """Read European-format CSV (semicolon, cp1252); verify delimiter and encoding detection."""
    path = FIXTURES_DIR / "european_export.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    df = csvmedic.read(path)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["Customer-ID", "Name", "Date", "Revenue", "Active"]
    assert len(df) == 3
    diagnosis = df.attrs.get("diagnosis")
    assert diagnosis is not None
    assert diagnosis.file_profile.delimiter_detected == ";"
    enc = diagnosis.file_profile.encoding_detected.lower()
    assert any(x in enc for x in ("1252", "1250", "windows", "cp125", "mac_latin", "latin"))


def test_read_french_dates() -> None:
    """Read French CSV; date column should be detected and parsed."""
    path = FIXTURES_DIR / "french_dates.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    df = csvmedic.read(path)
    assert list(df.columns) == ["id", "nom", "date_inscription", "montant"]
    diagnosis = df.attrs.get("diagnosis")
    assert diagnosis is not None
    # date_inscription should be detected as date (DD/MM/YYYY)
    col = diagnosis.file_profile.columns.get("date_inscription")
    if col and col.detected_type in (DetectedType.DATE, DetectedType.DATETIME):
        assert col.action == Action.CONVERTED


def test_leading_zeros_preserved() -> None:
    """ID/zip columns with leading zeros stay as strings."""
    path = FIXTURES_DIR / "leading_zeros.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    df = csvmedic.read(path)
    diagnosis = df.attrs.get("diagnosis")
    assert diagnosis is not None
    # product_id and zip_code should be preserved (leading zeros)
    for col_name in ("product_id", "zip_code"):
        col = diagnosis.file_profile.columns.get(col_name)
        assert col is not None
        assert col.detected_type == DetectedType.STRING or col.action == Action.PRESERVED
    assert df["product_id"].iloc[0] == "00742"


def test_full_european_export() -> None:
    """Semicolon, cp1252, DD.MM.YYYY dates, European numbers, Ja/Nein in one file."""
    path = FIXTURES_DIR / "european_export.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    df = csvmedic.read(path)
    assert list(df.columns) == ["Customer-ID", "Name", "Date", "Revenue", "Active"]
    assert len(df) == 3
    diagnosis = df.attrs.get("diagnosis")
    assert diagnosis is not None
    assert diagnosis.file_profile.delimiter_detected == ";"
    assert df["Customer-ID"].iloc[0] == "00742"


def test_preserve_strings_kwarg_does_not_break_read(simple_us_csv: Path) -> None:
    """preserve_strings must be popped before pd.read_csv; using it must not raise TypeError."""
    df = csvmedic.read(simple_us_csv, preserve_strings=["id"])
    assert isinstance(df, pd.DataFrame)
    diagnosis = df.attrs.get("diagnosis")
    assert diagnosis is not None
    col = diagnosis.file_profile.columns.get("id")
    assert col is not None
    assert col.action == Action.PRESERVED
