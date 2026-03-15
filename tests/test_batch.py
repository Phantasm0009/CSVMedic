"""Tests for read_batch and consensus detection."""

from pathlib import Path

import pandas as pd
import pytest

import csvmedic

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_read_batch_single_path() -> None:
    """read_batch with single path returns one DataFrame."""
    path = FIXTURES_DIR / "us_standard.csv"
    if not path.exists():
        pytest.skip("fixture not found")
    result = csvmedic.read_batch(path)
    assert len(result) == 1
    assert isinstance(result[0], pd.DataFrame)
    assert len(result[0]) >= 1


def test_read_batch_list_of_paths() -> None:
    """read_batch with list of paths returns one DataFrame per path."""
    paths = [
        FIXTURES_DIR / "us_standard.csv",
        FIXTURES_DIR / "leading_zeros.csv",
    ]
    paths = [p for p in paths if p.exists()]
    if len(paths) < 2:
        pytest.skip("need at least 2 fixtures")
    result = csvmedic.read_batch(paths)
    assert len(result) == len(paths)
    for i, df in enumerate(result):
        assert isinstance(df, pd.DataFrame), f"path {paths[i]}"


def test_read_batch_consensus_encoding_delimiter() -> None:
    """With use_consensus=True, all files get same encoding/delimiter from majority."""
    paths = [
        FIXTURES_DIR / "german_semicolon.csv",
        FIXTURES_DIR / "german_semicolon.csv",
    ]
    paths = [p for p in paths if p.exists()]
    if not paths:
        pytest.skip("fixture not found")
    result = csvmedic.read_batch(paths, use_consensus=True)
    assert len(result) == len(paths)
    for df in result:
        diag = df.attrs.get("diagnosis")
        assert diag is not None
        assert diag.file_profile.delimiter_detected == ";"


def test_read_batch_empty_list() -> None:
    """read_batch([]) returns []."""
    assert csvmedic.read_batch([]) == []
