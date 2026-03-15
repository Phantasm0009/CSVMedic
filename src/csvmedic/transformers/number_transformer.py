"""Apply number locale normalization to columns."""

from __future__ import annotations

import re

import pandas as pd

from csvmedic.diagnosis import TransformationRecord
from csvmedic.models import ColumnProfile


def _normalize_value(
    value: str, decimal_sep: str | None, thousands_sep: str | None
) -> float | int | None:
    """Convert formatted number string to float or int."""
    if not value or not str(value).strip():
        return None
    cleaned = re.sub(r"[€$£¥%\s]", "", str(value).strip())
    if thousands_sep:
        cleaned = cleaned.replace(thousands_sep, "")
    if decimal_sep:
        cleaned = cleaned.replace(decimal_sep, ".")
    try:
        f = float(cleaned)
        return int(f) if f == int(f) else f
    except ValueError:
        return None


def apply_number_conversion(
    df: pd.DataFrame,
    col_name: str,
    profile: ColumnProfile,
) -> tuple[pd.DataFrame, TransformationRecord]:
    """Apply number conversion. Returns (df, record)."""
    details = profile.details
    decimal_sep = details.get("decimal_separator")
    thousands_sep = details.get("thousands_separator")
    d_sep = decimal_sep if isinstance(decimal_sep, str) else None
    t_sep = thousands_sep if isinstance(thousands_sep, str) else None

    before_dtype = str(df[col_name].dtype)
    series = df[col_name].astype(str)
    converted = series.apply(lambda v: _normalize_value(str(v), d_sep, t_sep))
    rows_affected = converted.notna().sum()
    rows_failed = converted.isna().sum()

    df[col_name] = pd.to_numeric(converted, errors="coerce")
    after_dtype = "float64"

    record = TransformationRecord(
        column=col_name,
        step="number_normalize",
        before_dtype=before_dtype,
        after_dtype=after_dtype,
        rows_affected=int(rows_affected),
        rows_failed=int(rows_failed),
        details=f"decimal={decimal_sep!r}, thousands={thousands_sep!r}",
    )
    return (df, record)
