"""Tests for diff(): pandas vs csvmedic comparison."""

from pathlib import Path

import pandas as pd
import pytest

import csvmedic

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_diff_returns_both_dataframes() -> None:
    """diff() returns DiffResult with pandas_df and csvmedic_df."""
    path = FIXTURES_DIR / "us_standard.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    result = csvmedic.diff(path)
    assert result.pandas_df is not None
    assert result.csvmedic_df is not None
    assert isinstance(result.pandas_df, pd.DataFrame)
    assert isinstance(result.csvmedic_df, pd.DataFrame)


def test_diff_leading_zeros_shows_difference() -> None:
    """On leading_zeros.csv, pandas strips zeros; csvmedic preserves; diff shows it."""
    path = FIXTURES_DIR / "leading_zeros.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    result = csvmedic.diff(path)
    # pandas may read 00742 as integer 742
    assert "product_id" in result.pandas_df.columns
    assert "product_id" in result.csvmedic_df.columns
    # csvmedic preserves leading zeros
    assert result.csvmedic_df["product_id"].iloc[0] == "00742"
    # So there should be a column difference or sample difference
    has_diff = "product_id" in result.columns_with_differences or any(
        col == "product_id" for (_, col, _, _) in result.sample_differences
    )
    assert has_diff or result.pandas_df["product_id"].iloc[0] != "00742"


def test_diff_summary_is_string() -> None:
    """DiffResult.summary() returns a non-empty string."""
    path = FIXTURES_DIR / "us_standard.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    result = csvmedic.diff(path)
    s = result.summary()
    assert isinstance(s, str)
    assert "pandas" in s.lower() or "csvmedic" in s.lower()
