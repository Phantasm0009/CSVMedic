"""Apply detected date formats to columns."""

from __future__ import annotations

import pandas as pd

from csvmedic.diagnosis import TransformationRecord
from csvmedic.models import ColumnProfile, DetectedType


def _parse_value(value: str, fmt: str | None, dayfirst: bool | None) -> pd.Timestamp | None:
    """Parse a single value to datetime. Returns None on failure."""
    if not value or not str(value).strip():
        return None
    value = str(value).strip()
    if fmt is None or fmt == "named_month":
        try:
            res = pd.to_datetime(value, errors="coerce")
            return None if pd.isna(res) else res  # type: ignore[return-value]
        except Exception:
            return None
    if fmt == "%Y%m%d":
        if len(value) == 8 and value.isdigit():
            try:
                return pd.Timestamp(int(value[:4]), int(value[4:6]), int(value[6:8]))
            except (ValueError, TypeError):
                pass
        return None
    try:
        result = pd.to_datetime(value, format=fmt, errors="coerce")
        if pd.isna(result):
            return None
        return result  # type: ignore[return-value]
    except Exception:
        return None


def apply_date_conversion(
    df: pd.DataFrame,
    col_name: str,
    profile: ColumnProfile,
) -> tuple[pd.DataFrame, TransformationRecord]:
    """Apply date conversion to the column. Returns (df, record)."""
    details = profile.details
    fmt = details.get("format_detected")
    dayfirst = details.get("dayfirst")
    if fmt is None and profile.detected_type in (DetectedType.DATE, DetectedType.DATETIME):
        fmt = "%Y-%m-%d"  # fallback
    fmt_s = fmt if isinstance(fmt, str) else None
    dayfirst_b = dayfirst if isinstance(dayfirst, bool) else None

    before_dtype = str(df[col_name].dtype)
    series = df[col_name].astype(str)
    converted = series.apply(lambda v: _parse_value(str(v), fmt_s, dayfirst_b))
    rows_affected = converted.notna().sum()
    rows_failed = converted.isna().sum() - series.isin(["", "nan", "None"]).sum()

    df[col_name] = pd.to_datetime(converted, errors="coerce")

    record = TransformationRecord(
        column=col_name,
        step="date_parse",
        before_dtype=before_dtype,
        after_dtype="datetime64[ns]",
        rows_affected=int(rows_affected),
        rows_failed=int(max(0, rows_failed)),
        details=f"format={fmt!r}, dayfirst={dayfirst}",
    )
    return (df, record)
