"""Boolean variant detection across locales."""

from __future__ import annotations

from dataclasses import dataclass

# (true_values, false_values) per locale
BOOLEAN_MAP: list[tuple[list[str], list[str]]] = [
    (["true", "yes", "y", "1", "on"], ["false", "no", "n", "0", "off"]),
    (["ja", "j", "jaa"], ["nein", "n"]),
    (["oui", "o", "vrai"], ["non", "faux"]),
    (["sí", "si", "s"], ["no"]),
    (["vero", "sì"], ["falso"]),
    (["waar"], ["onwaar"]),
]

ALL_TRUE: set[str] = set()
ALL_FALSE: set[str] = set()
for trues, falses in BOOLEAN_MAP:
    ALL_TRUE.update(trues)
    ALL_FALSE.update(falses)


@dataclass
class BooleanDetectionResult:
    """Result of boolean detection."""

    is_boolean: bool
    confidence: float
    true_variants: list[str]
    false_variants: list[str]


def detect_boolean_column(values: list[str]) -> BooleanDetectionResult:
    """Detect if column is boolean; require >=90% of non-null values to match."""
    filtered = [str(v).strip().lower() for v in values if v is not None and str(v).strip()]
    if not filtered:
        return BooleanDetectionResult(False, 0.0, [], [])

    unique = set(filtered)
    if len(unique) > 2:
        return BooleanDetectionResult(False, 0.0, [], [])

    allowed = ALL_TRUE | ALL_FALSE
    match_count = sum(1 for v in filtered if v in allowed)
    ratio = match_count / len(filtered)

    if ratio < 0.9:
        return BooleanDetectionResult(False, ratio, [], [])

    true_found = [v for v in unique if v in ALL_TRUE]
    false_found = [v for v in unique if v in ALL_FALSE]
    if not true_found or not false_found:
        return BooleanDetectionResult(False, ratio, [], [])

    return BooleanDetectionResult(
        is_boolean=True,
        confidence=min(1.0, ratio + 0.05),
        true_variants=true_found,
        false_variants=false_found,
    )
