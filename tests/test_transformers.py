"""Tests for transformers."""

import pandas as pd
import pytest

from csvmedic.models import Action, ColumnProfile, DetectedType
from csvmedic.transformers.boolean_transformer import apply_boolean_conversion
from csvmedic.transformers.date_transformer import apply_date_conversion
from csvmedic.transformers.number_transformer import apply_number_conversion


def test_date_transformer() -> None:
    df = pd.DataFrame({"d": ["2025-03-14", "2024-01-01"]})
    profile = ColumnProfile(
        name="d",
        original_dtype="object",
        detected_type=DetectedType.DATE,
        confidence=1.0,
        action=Action.CONVERTED,
        details={"format_detected": "%Y-%m-%d", "dayfirst": None},
    )
    out, record = apply_date_conversion(df, "d", profile)
    assert record.step == "date_parse"
    assert pd.api.types.is_datetime64_any_dtype(out["d"])


def test_number_transformer_us() -> None:
    df = pd.DataFrame({"n": ["1,234.56", "789.00"]})
    profile = ColumnProfile(
        name="n",
        original_dtype="object",
        detected_type=DetectedType.FLOAT,
        confidence=1.0,
        action=Action.CONVERTED,
        details={"decimal_separator": ".", "thousands_separator": ","},
    )
    out, record = apply_number_conversion(df, "n", profile)
    assert record.step == "number_normalize"
    assert out["n"].iloc[0] == pytest.approx(1234.56)


def test_boolean_transformer() -> None:
    df = pd.DataFrame({"b": ["Yes", "No", "Yes"]})
    profile = ColumnProfile(
        name="b",
        original_dtype="object",
        detected_type=DetectedType.BOOLEAN,
        confidence=1.0,
        action=Action.CONVERTED,
        details={"true_variants": ["yes"], "false_variants": ["no"]},
    )
    out, record = apply_boolean_conversion(df, "b", profile)
    assert record.step == "bool_convert"
    assert out["b"].iloc[0] == True  # noqa: E712
    assert out["b"].iloc[1] == False  # noqa: E712
