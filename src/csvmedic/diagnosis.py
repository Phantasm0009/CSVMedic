"""Diagnosis dataclass and TransformationRecord attached to DataFrame."""

from __future__ import annotations

from dataclasses import dataclass

from csvmedic.models import ColumnProfile, FileProfile


@dataclass
class TransformationRecord:
    """Log entry for a single transformation step."""

    column: str
    step: str
    before_dtype: str
    after_dtype: str
    rows_affected: int
    rows_failed: int
    details: str


@dataclass
class Diagnosis:
    """
    Attached to the returned DataFrame as df.diagnosis.
    Contains the full FileProfile plus transformation log.
    """

    file_profile: FileProfile
    transformations: list[TransformationRecord]
    elapsed_seconds: float

    @property
    def columns(self) -> dict[str, ColumnProfile]:
        """Delegate to file_profile.columns."""
        return self.file_profile.columns

    def __repr__(self) -> str:
        """Pretty-print the diagnosis for terminal output."""
        lines = [
            f"csvmedic Diagnosis ({self.elapsed_seconds:.2f}s)",
            f"  Encoding: {self.file_profile.encoding_detected} "
            f"(confidence: {self.file_profile.encoding_confidence:.0%})",
            f"  Delimiter: {repr(self.file_profile.delimiter_detected)}",
            f"  Shape: {self.file_profile.row_count} rows × "
            f"{self.file_profile.column_count} columns",
            "",
        ]
        icon_map = {
            "converted": "✓",
            "preserved": "—",
            "ambiguous": "?",
            "skipped": "·",
            "failed": "✗",
        }
        for name, col in self.file_profile.columns.items():
            icon = icon_map.get(col.action.value, "·")
            lines.append(
                f"  {icon} {name}: {col.detected_type.value} "
                f"(confidence: {col.confidence:.0%}, {col.action.value})"
            )
            if col.details:
                for k, v in col.details.items():
                    if k != "sample_values":
                        lines.append(f"      {k}: {v}")
        return "\n".join(lines)
