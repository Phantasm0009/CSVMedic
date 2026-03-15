"""Leading-zero preservation and string heuristics. Phase 3 stub; full impl in Phase 4."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StringPreservationResult:
    """Result of string preservation check."""

    should_preserve: bool
    reason: str
    sample_values: list[str]


def detect_string_preservation(values: list[str]) -> StringPreservationResult:
    """Detect if column should be preserved as string (e.g. leading zeros). Stub: returns False."""
    sample = [v for v in values if v and str(v).strip()][:10]
    # Minimal check: >10% leading zeros -> preserve (Phase 4 will implement fully)
    leading_zero_count = sum(
        1 for v in sample if str(v).strip().startswith("0") and str(v).strip().isdigit()
    )
    if sample and leading_zero_count / len(sample) > 0.1:
        return StringPreservationResult(
            should_preserve=True,
            reason="leading_zeros_detected",
            sample_values=sample[:5],
        )
    return StringPreservationResult(should_preserve=False, reason="", sample_values=sample[:5])
