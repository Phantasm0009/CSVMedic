"""Pydantic-free dataclasses: ColumnProfile, FileProfile."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import cast


class DetectedType(Enum):
    """Possible detected column types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class Action(Enum):
    """What csvmedic did (or will do) with a column."""

    CONVERTED = "converted"
    PRESERVED = "preserved"
    AMBIGUOUS = "ambiguous"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class ColumnProfile:
    """Detection result for a single column."""

    name: str
    original_dtype: str
    detected_type: DetectedType
    confidence: float
    action: Action
    details: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary (for JSON export)."""
        return {
            "name": self.name,
            "original_dtype": self.original_dtype,
            "detected_type": self.detected_type.value,
            "confidence": self.confidence,
            "action": self.action.value,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> ColumnProfile:
        """Deserialize from dictionary (e.g. from JSON schema)."""
        details = d.get("details", {})
        return cls(
            name=str(d["name"]),
            original_dtype=str(d["original_dtype"]),
            detected_type=DetectedType(str(d["detected_type"])),
            confidence=cast(float, d["confidence"]),
            action=Action(str(d["action"])),
            details=dict(cast(dict[str, object], details)) if isinstance(details, dict) else {},
        )


@dataclass
class FileProfile:
    """Complete analysis result for a file."""

    filepath: str | None
    encoding_detected: str
    encoding_confidence: float
    delimiter_detected: str
    has_header: bool
    row_count: int
    column_count: int
    columns: dict[str, ColumnProfile]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary (for JSON export)."""
        return {
            "filepath": self.filepath,
            "encoding_detected": self.encoding_detected,
            "encoding_confidence": self.encoding_confidence,
            "delimiter_detected": self.delimiter_detected,
            "has_header": self.has_header,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": {k: v.to_dict() for k, v in self.columns.items()},
            "warnings": self.warnings,
        }

    def summary(self) -> str:
        """Human-readable summary string."""
        return (
            f"FileProfile(encoding={self.encoding_detected!r}, "
            f"delimiter={self.delimiter_detected!r}, "
            f"rows={self.row_count}, columns={self.column_count})"
        )

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> FileProfile:
        """Deserialize from dictionary (e.g. from JSON schema)."""
        columns_raw = d.get("columns", {})
        if not isinstance(columns_raw, dict):
            columns_raw = {}
        columns = {
            str(k): ColumnProfile.from_dict(v)
            for k, v in columns_raw.items()
            if isinstance(v, dict)
        }
        warnings_val = d.get("warnings", [])
        return cls(
            filepath=str(d["filepath"]) if d.get("filepath") else None,
            encoding_detected=str(d["encoding_detected"]),
            encoding_confidence=cast(float, d["encoding_confidence"]),
            delimiter_detected=str(d["delimiter_detected"]),
            has_header=bool(d.get("has_header", True)),
            row_count=cast(int, d.get("row_count", 0)),
            column_count=cast(int, d.get("column_count", len(columns))),
            columns=columns,
            warnings=list(warnings_val) if isinstance(warnings_val, list) else [],
        )
