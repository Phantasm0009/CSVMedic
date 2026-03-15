"""String cleaning: strip whitespace, preserve IDs."""

from __future__ import annotations

import pandas as pd

from csvmedic.diagnosis import TransformationRecord
from csvmedic.models import ColumnProfile


def apply_string_cleaning(
    df: pd.DataFrame,
    col_name: str,
    profile: ColumnProfile,
) -> tuple[pd.DataFrame, TransformationRecord]:
    """Strip whitespace from string column. Returns (df, record)."""
    before_dtype = str(df[col_name].dtype)
    series = df[col_name].astype(str).str.strip()
    rows_affected = series.notna().sum()

    df = df.copy()
    df[col_name] = series

    record = TransformationRecord(
        column=col_name,
        step="string_clean",
        before_dtype=before_dtype,
        after_dtype="object",
        rows_affected=int(rows_affected),
        rows_failed=0,
        details="strip whitespace",
    )
    return (df, record)
