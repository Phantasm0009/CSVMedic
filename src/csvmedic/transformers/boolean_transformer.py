"""Normalize boolean columns to True/False."""

from __future__ import annotations

import pandas as pd

from csvmedic.detectors.booleans import ALL_FALSE, ALL_TRUE
from csvmedic.diagnosis import TransformationRecord
from csvmedic.models import ColumnProfile


def apply_boolean_conversion(
    df: pd.DataFrame,
    col_name: str,
    profile: ColumnProfile,
) -> tuple[pd.DataFrame, TransformationRecord]:
    """Map boolean variants to True/False. Returns (df, record)."""
    details = profile.details
    raw_true = details.get("true_variants", [])
    raw_false = details.get("false_variants", [])
    if not isinstance(raw_true, (list, tuple)):
        raw_true = []
    if not isinstance(raw_false, (list, tuple)):
        raw_false = []
    true_variants = set(x for x in raw_true if isinstance(x, str))
    false_variants = set(x for x in raw_false if isinstance(x, str))
    if not true_variants:
        true_variants = ALL_TRUE
    if not false_variants:
        false_variants = ALL_FALSE

    before_dtype = str(df[col_name].dtype)
    series = df[col_name].astype(str).str.strip().str.lower()

    def _map_val(v: str) -> bool | object:
        if v in true_variants:
            return True
        if v in false_variants:
            return False
        return pd.NA

    mapped = series.map(_map_val)
    rows_affected = mapped.notna().sum()
    rows_failed = mapped.isna().sum() - series.isin(["", "nan"]).sum()

    df = df.copy()
    df[col_name] = mapped

    record = TransformationRecord(
        column=col_name,
        step="bool_convert",
        before_dtype=before_dtype,
        after_dtype="bool",
        rows_affected=int(rows_affected),
        rows_failed=int(max(0, rows_failed)),
        details=f"true={list(true_variants)[:3]!r}, false={list(false_variants)[:3]!r}",
    )
    return (df, record)
