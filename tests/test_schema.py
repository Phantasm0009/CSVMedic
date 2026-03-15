"""Tests for schema pinning: save_schema, load_schema, read with schema=."""

from pathlib import Path

import pytest

import csvmedic

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_save_and_load_schema(tmp_path: Path) -> None:
    """save_schema and load_schema round-trip."""
    path = FIXTURES_DIR / "us_standard.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    df = csvmedic.read(path)
    profile = df.attrs["diagnosis"].file_profile
    schema_path = tmp_path / "us_standard.csvmedic.json"
    csvmedic.save_schema(profile, schema_path)
    assert schema_path.exists()
    loaded = csvmedic.load_schema(schema_path)
    assert loaded.encoding_detected == profile.encoding_detected
    assert loaded.delimiter_detected == profile.delimiter_detected
    assert loaded.column_count == profile.column_count
    assert set(loaded.columns) == set(profile.columns)


def test_read_with_schema_path(tmp_path: Path) -> None:
    """read(path, schema=json_path) uses cached schema and produces same result."""
    path = FIXTURES_DIR / "leading_zeros.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    df1 = csvmedic.read(path)
    profile = df1.attrs["diagnosis"].file_profile
    schema_path = tmp_path / "leading_zeros.csvmedic.json"
    csvmedic.save_schema(profile, schema_path)
    df2 = csvmedic.read(path, schema=schema_path)
    assert list(df1.columns) == list(df2.columns)
    assert len(df1) == len(df2)
    assert df2["product_id"].iloc[0] == "00742"


def test_schema_path_for_csv() -> None:
    """schema_path_for_csv returns same dir, name.csvmedic.json."""
    p = csvmedic.schema_path_for_csv("/data/exports/foo.csv")
    assert p.name == "foo.csvmedic.json"
    assert p.parent.name == "exports"
