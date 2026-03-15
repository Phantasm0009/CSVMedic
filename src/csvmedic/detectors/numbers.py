"""
Detect number formatting locale (decimal and thousands separators).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class NumberDetectionResult:
    """Result of number locale detection for a single column."""

    is_numeric: bool
    decimal_separator: str | None
    thousands_separator: str | None
    locale_hint: str | None
    confidence: float
    is_integer: bool
    has_leading_zeros: bool
    sample_values: list[str]


def _classify_separators(value: str) -> tuple[str | None, str | None]:
    """Determine decimal and thousands separators for a single numeric string."""
    cleaned = re.sub(r"[€$£¥%\s]", "", value.strip())
    if not re.search(r"\d", cleaned):
        return (None, None)
    has_period = "." in cleaned
    has_comma = "," in cleaned
    has_apostrophe = "'" in cleaned

    if has_period and has_comma:
        last_period = cleaned.rfind(".")
        last_comma = cleaned.rfind(",")
        if last_period > last_comma:
            return (".", ",")
        return (",", ".")

    if has_period and not has_comma:
        after = cleaned.split(".")[-1]
        if len(after) == 3 and cleaned.count(".") == 1:
            return (".", None)
        if len(after) == 3 and cleaned.count(".") > 1:
            return (None, ".")
        return (".", None)

    if has_comma and not has_period:
        after = cleaned.split(",")[-1]
        if len(after) == 3 and cleaned.count(",") == 1:
            return (None, ",")
        if len(after) == 3 and cleaned.count(",") > 1:
            return (None, ",")
        return (",", None)

    if has_apostrophe and has_period:
        return (".", "'")
    if has_apostrophe:
        return (None, "'")

    # Only digits, optional minus
    if re.fullmatch(r"-?\d+", cleaned):
        return (None, None)
    return (None, None)


def _normalize_to_float(
    value: str, decimal_sep: str | None, thousands_sep: str | None
) -> float | None:
    """Convert a formatted number string to float."""
    cleaned = re.sub(r"[€$£¥%\s]", "", value.strip())
    if thousands_sep:
        cleaned = cleaned.replace(thousands_sep, "")
    if decimal_sep:
        cleaned = cleaned.replace(decimal_sep, ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def detect_number_column(values: list[str]) -> NumberDetectionResult:
    """Analyze string values to detect number formatting and leading zeros."""
    filtered = [str(v).strip() for v in values if v and str(v).strip()]
    if not filtered:
        return NumberDetectionResult(
            is_numeric=False,
            decimal_separator=None,
            thousands_separator=None,
            locale_hint=None,
            confidence=0.0,
            is_integer=False,
            has_leading_zeros=False,
            sample_values=[],
        )

    # Leading zeros: >10% of values start with 0 and are all digits
    leading_zero_count = sum(1 for v in filtered if re.match(r"^0\d*$", v) and v.isdigit())
    if leading_zero_count / len(filtered) > 0.1:
        return NumberDetectionResult(
            is_numeric=True,
            decimal_separator=None,
            thousands_separator=None,
            locale_hint=None,
            confidence=1.0,
            is_integer=False,
            has_leading_zeros=True,
            sample_values=filtered[:5],
        )

    # Classify each value (include plain integers)
    results: list[tuple[str | None, str | None]] = []
    for v in filtered:
        cleaned = re.sub(r"[€$£¥%\s]", "", v)
        dec, thou = _classify_separators(v)
        if dec is not None or thou is not None or re.fullmatch(r"-?\d+", cleaned):
            results.append((dec, thou))

    if not results:
        return NumberDetectionResult(
            is_numeric=False,
            decimal_separator=None,
            thousands_separator=None,
            locale_hint=None,
            confidence=0.0,
            is_integer=False,
            has_leading_zeros=False,
            sample_values=filtered[:5],
        )

    # Consensus: most common (decimal, thousands) pair
    from collections import Counter

    pair_counts = Counter(results)
    (decimal_sep, thousands_sep) = pair_counts.most_common(1)[0][0]
    if decimal_sep is None and thousands_sep is None:
        # All plain integers
        decimal_sep = None
        thousands_sep = None

    # Resolve locale hint
    locale_hint = None
    if decimal_sep == "." and thousands_sep == ",":
        locale_hint = "en_US"
    elif decimal_sep == "," and thousands_sep == ".":
        locale_hint = "de_DE"
    elif decimal_sep == "," and thousands_sep == " ":
        locale_hint = "fr_FR"
    elif thousands_sep == "'":
        locale_hint = "de_CH"

    # Validate: try parsing all with this locale
    parse_ok = 0
    all_integer = True
    for v in filtered:
        n = _normalize_to_float(v, decimal_sep, thousands_sep)
        if n is not None:
            parse_ok += 1
            if n != int(n):
                all_integer = False
        else:
            # Plain integer without separators
            try:
                int(re.sub(r"[^\d-]", "", v))
                parse_ok += 1
            except ValueError:
                pass

    total = len(filtered)
    confidence = parse_ok / total if total else 0.0
    if confidence < 0.8:
        return NumberDetectionResult(
            is_numeric=False,
            decimal_separator=decimal_sep,
            thousands_separator=thousands_sep,
            locale_hint=locale_hint,
            confidence=confidence,
            is_integer=False,
            has_leading_zeros=False,
            sample_values=filtered[:5],
        )

    return NumberDetectionResult(
        is_numeric=True,
        decimal_separator=decimal_sep,
        thousands_separator=thousands_sep,
        locale_hint=locale_hint,
        confidence=min(1.0, confidence + 0.1),
        is_integer=all_integer,
        has_leading_zeros=False,
        sample_values=filtered[:5],
    )
