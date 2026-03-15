"""Tests for confidence scoring."""

from csvmedic.confidence import clamp_confidence


def test_clamp_confidence_basic() -> None:
    assert clamp_confidence(0.5) == 0.5
    assert clamp_confidence(0.0) == 0.0
    assert clamp_confidence(1.0) == 1.0


def test_clamp_confidence_above_max() -> None:
    assert clamp_confidence(1.5) == 1.0


def test_clamp_confidence_below_min() -> None:
    assert clamp_confidence(-0.2) == 0.0


def test_clamp_confidence_custom_bounds() -> None:
    assert clamp_confidence(0.5, min_val=0.2, max_val=0.8) == 0.5
    assert clamp_confidence(0.1, min_val=0.2, max_val=0.8) == 0.2
    assert clamp_confidence(0.9, min_val=0.2, max_val=0.8) == 0.8
