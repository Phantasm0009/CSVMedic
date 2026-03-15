"""Confidence scoring for ambiguous detections."""

from __future__ import annotations


def clamp_confidence(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a confidence score to [min_val, max_val]."""
    return max(min_val, min(max_val, value))
