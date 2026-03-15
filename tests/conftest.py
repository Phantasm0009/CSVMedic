"""Shared fixtures: sample CSV generators."""

from pathlib import Path

import pytest


@pytest.fixture
def temp_csv_dir(tmp_path: Path) -> Path:
    """Return a temporary directory for writing test CSV files."""
    return tmp_path


@pytest.fixture
def simple_us_csv(temp_csv_dir: Path) -> Path:
    """A simple US-format CSV (UTF-8, comma-delimited) for basic read test."""
    path = temp_csv_dir / "simple_us.csv"
    path.write_text(
        "id,name,value\n1,Alice,100.5\n2,Bob,200.0\n3,Charlie,300.25\n",
        encoding="utf-8",
    )
    return path
