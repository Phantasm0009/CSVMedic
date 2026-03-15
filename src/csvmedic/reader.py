"""
Main orchestrator: encoding -> dialect -> read with dtype=str -> per-column detection -> diagnosis.

Read-once pipeline: read byte sample (or full for non-seekable) once; use for encoding and
dialect; then pandas reads from path/buffer (or StringIO(decoded) if source was consumed).
"""

from __future__ import annotations

import io
import time
from pathlib import Path
from typing import IO, Any, cast

import pandas as pd

from csvmedic.detectors.booleans import detect_boolean_column
from csvmedic.detectors.dates import detect_date_column
from csvmedic.detectors.dialect import detect_dialect
from csvmedic.detectors.encoding import (
    DEFAULT_ENCODING_SAMPLE_BYTES,
    detect_encoding,
)
from csvmedic.detectors.numbers import detect_number_column
from csvmedic.detectors.strings import detect_string_preservation
from csvmedic.diagnosis import Diagnosis, TransformationRecord
from csvmedic.models import Action, ColumnProfile, DetectedType, FileProfile
from csvmedic.schema import load_schema
from csvmedic.transformers.boolean_transformer import apply_boolean_conversion
from csvmedic.transformers.date_transformer import apply_date_conversion
from csvmedic.transformers.number_transformer import apply_number_conversion


def _read_byte_sample(
    filepath_or_buffer: str | Path | IO[bytes],
    sample_size: int = DEFAULT_ENCODING_SAMPLE_BYTES,
) -> tuple[bytes, bool]:
    """
    Read bytes from path or buffer. Returns (bytes, use_decoded_for_csv).
    use_decoded_for_csv is True when the source was fully consumed (non-seekable buffer),
    so the caller must pass decoded content to pandas via StringIO.
    """
    if isinstance(filepath_or_buffer, (str, Path)):
        path = Path(filepath_or_buffer)
        with open(path, "rb") as f:
            return (f.read(sample_size), False)
    # file-like
    buf = filepath_or_buffer
    seekable = getattr(buf, "seek", None) is not None and callable(buf.seek)
    if seekable:
        raw = buf.read(sample_size)
        buf.seek(0)
        return (raw if isinstance(raw, bytes) else raw.encode("utf-8"), False)
    # Non-seekable: read all (single read, then use decoded for dialect + pandas)
    raw = buf.read()
    return (raw if isinstance(raw, bytes) else raw.encode("utf-8"), True)


class MedicReader:
    """
    Stateful reader that can be configured and reused.
    The module-level read() function creates a temporary instance.
    """

    def __init__(
        self,
        sample_rows: int = 1000,
        confidence_threshold: float = 0.75,
    ) -> None:
        self.sample_rows = sample_rows
        self.confidence_threshold = confidence_threshold

    def read(
        self,
        filepath_or_buffer: str | Path | IO[bytes],
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Read CSV with diagnosis. Uses encoding/dialect detection when not overridden."""
        start_time = time.monotonic()
        transformations: list[TransformationRecord] = []

        # Optional schema pinning: load FileProfile from path or use provided profile
        schema_arg = kwargs.pop("schema", None)
        schema_profile: FileProfile | None = None
        if schema_arg is not None:
            if isinstance(schema_arg, (str, Path)):
                schema_profile = load_schema(schema_arg)
            elif isinstance(schema_arg, FileProfile):
                schema_profile = schema_arg
            else:
                raise TypeError("schema must be a path (str | Path) or FileProfile")

        # Read once: byte sample (or full for non-seekable buffer); reuse for encoding + dialect
        bytes_sample, use_decoded_for_csv = _read_byte_sample(filepath_or_buffer)

        encoding_override = kwargs.pop("encoding", None)
        if encoding_override is not None:
            encoding = encoding_override
            encoding_confidence = 1.0
        elif schema_profile is not None:
            encoding = schema_profile.encoding_detected
            encoding_confidence = schema_profile.encoding_confidence
        else:
            enc_result = detect_encoding(bytes_sample)
            encoding = enc_result.encoding
            encoding_confidence = enc_result.confidence

        decoded_sample = bytes_sample.decode(encoding, errors="replace")

        delimiter_override = kwargs.pop("delimiter", None)
        if delimiter_override is not None:
            delimiter = delimiter_override
            has_header = True
        elif schema_profile is not None:
            delimiter = schema_profile.delimiter_detected
            has_header = schema_profile.has_header
        else:
            dialect_result = detect_dialect(
                None, encoding, sample_text=decoded_sample
            )
            delimiter = dialect_result.delimiter
            has_header = dialect_result.has_header

        na_values = kwargs.pop("na_values", None)
        preserve_strings = kwargs.pop("preserve_strings", None) or []
        force_dayfirst = kwargs.pop("dayfirst", None)

        csv_source: str | Path | IO[bytes] | io.StringIO
        if use_decoded_for_csv:
            csv_source = io.StringIO(decoded_sample)
            read_kw = {
                "sep": delimiter,
                "dtype": str,
                "keep_default_na": True,
                "na_values": na_values,
                "header": 0 if has_header else None,
                **kwargs,
            }
        else:
            csv_source = filepath_or_buffer
            read_kw = {
                "encoding": encoding,
                "sep": delimiter,
                "dtype": str,
                "keep_default_na": True,
                "na_values": na_values,
                "header": 0 if has_header else None,
                **kwargs,
            }

        df_raw = pd.read_csv(csv_source, **read_kw)

        column_profiles: dict[str, ColumnProfile] = {}
        resolved_dayfirst: bool | None = None

        for col_name in df_raw.columns:
            # Schema pinning: use cached column profile if present
            if schema_profile is not None and col_name in schema_profile.columns:
                column_profiles[col_name] = schema_profile.columns[col_name]
                prof = schema_profile.columns[col_name]
                if prof.detected_type in (DetectedType.DATE, DetectedType.DATETIME):
                    dayfirst_val = prof.details.get("dayfirst")
                    if resolved_dayfirst is None and dayfirst_val is not None:
                        resolved_dayfirst = bool(dayfirst_val)
                continue

            raw_col = df_raw[col_name].dropna().head(self.sample_rows).astype(str)
            sample: list[str] = [str(x) for x in raw_col]

            if not sample:
                column_profiles[col_name] = ColumnProfile(
                    name=col_name,
                    original_dtype="object",
                    detected_type=DetectedType.UNKNOWN,
                    confidence=0.0,
                    action=Action.SKIPPED,
                )
                continue

            if col_name in preserve_strings:
                column_profiles[col_name] = ColumnProfile(
                    name=col_name,
                    original_dtype="object",
                    detected_type=DetectedType.STRING,
                    confidence=1.0,
                    action=Action.PRESERVED,
                    details={"reason": "user_specified"},
                )
                continue

            string_result = detect_string_preservation(sample)
            if string_result.should_preserve:
                column_profiles[col_name] = ColumnProfile(
                    name=col_name,
                    original_dtype="object",
                    detected_type=DetectedType.STRING,
                    confidence=1.0,
                    action=Action.PRESERVED,
                    details={
                        "reason": string_result.reason,
                        "sample_values": string_result.sample_values[:5],
                    },
                )
                continue

            bool_result = detect_boolean_column(sample)
            if bool_result.is_boolean and bool_result.confidence >= self.confidence_threshold:
                column_profiles[col_name] = ColumnProfile(
                    name=col_name,
                    original_dtype="object",
                    detected_type=DetectedType.BOOLEAN,
                    confidence=bool_result.confidence,
                    action=Action.CONVERTED,
                    details={
                        "true_variants": bool_result.true_variants,
                        "false_variants": bool_result.false_variants,
                    },
                )
                continue

            effective_dayfirst = force_dayfirst
            date_result = detect_date_column(
                sample,
                column_name=col_name,
                other_column_dayfirst=resolved_dayfirst if effective_dayfirst is None else None,
            )
            if date_result.is_date and date_result.confidence >= self.confidence_threshold:
                if effective_dayfirst is None:
                    effective_dayfirst = date_result.dayfirst
                if resolved_dayfirst is None and date_result.dayfirst is not None:
                    resolved_dayfirst = date_result.dayfirst
                column_profiles[col_name] = ColumnProfile(
                    name=col_name,
                    original_dtype="object",
                    detected_type=DetectedType.DATETIME
                    if (date_result.format_string or "").count(":")
                    else DetectedType.DATE,
                    confidence=date_result.confidence,
                    action=Action.CONVERTED,
                    details={
                        "format_detected": date_result.format_string,
                        "dayfirst": effective_dayfirst,
                        "ambiguous_count": date_result.ambiguous_count,
                        "unambiguous_count": date_result.unambiguous_count,
                        "disambiguation_method": date_result.disambiguation_method,
                        "sample_values": date_result.sample_values[:5],
                    },
                )
                continue

            num_result = detect_number_column(sample)
            if num_result.is_numeric and num_result.confidence >= self.confidence_threshold:
                if num_result.has_leading_zeros:
                    column_profiles[col_name] = ColumnProfile(
                        name=col_name,
                        original_dtype="object",
                        detected_type=DetectedType.STRING,
                        confidence=1.0,
                        action=Action.PRESERVED,
                        details={
                            "reason": "leading_zeros_detected",
                            "sample_values": num_result.sample_values[:5],
                        },
                    )
                else:
                    column_profiles[col_name] = ColumnProfile(
                        name=col_name,
                        original_dtype="object",
                        detected_type=DetectedType.INTEGER
                        if num_result.is_integer
                        else DetectedType.FLOAT,
                        confidence=num_result.confidence,
                        action=Action.CONVERTED,
                        details={
                            "locale_detected": num_result.locale_hint,
                            "decimal_separator": num_result.decimal_separator,
                            "thousands_separator": num_result.thousands_separator,
                            "sample_values": num_result.sample_values[:5],
                        },
                    )
                continue

            column_profiles[col_name] = ColumnProfile(
                name=col_name,
                original_dtype="object",
                detected_type=DetectedType.STRING,
                confidence=1.0,
                action=Action.SKIPPED,
            )

        df = df_raw.copy()
        for col_name, profile in column_profiles.items():
            if profile.action != Action.CONVERTED:
                continue
            if profile.detected_type in (DetectedType.DATE, DetectedType.DATETIME):
                df, record = apply_date_conversion(df, col_name, profile)
                transformations.append(record)
            elif profile.detected_type in (DetectedType.FLOAT, DetectedType.INTEGER):
                df, record = apply_number_conversion(df, col_name, profile)
                transformations.append(record)
            elif profile.detected_type == DetectedType.BOOLEAN:
                df, record = apply_boolean_conversion(df, col_name, profile)
                transformations.append(record)

        filepath_str: str | None = None
        if isinstance(filepath_or_buffer, (str, Path)):
            filepath_str = str(filepath_or_buffer)

        file_profile = FileProfile(
            filepath=filepath_str,
            encoding_detected=encoding,
            encoding_confidence=encoding_confidence,
            delimiter_detected=delimiter,
            has_header=has_header,
            row_count=len(df),
            column_count=len(df.columns),
            columns=column_profiles,
        )

        diagnosis = Diagnosis(
            file_profile=file_profile,
            transformations=transformations,
            elapsed_seconds=time.monotonic() - start_time,
        )
        df.attrs["diagnosis"] = diagnosis
        return cast(pd.DataFrame, df)


def read(
    filepath_or_buffer: str | Path | IO[bytes],
    *,
    encoding: str | None = None,
    delimiter: str | None = None,
    date_format: str | dict[str, str] | None = None,
    number_locale: str | None = None,
    dayfirst: bool | None = None,
    preserve_strings: list[str] | None = None,
    schema: str | Path | FileProfile | None = None,
    sample_rows: int = 1000,
    confidence_threshold: float = 0.75,
    na_values: list[str] | None = None,
    **pandas_kwargs: Any,
) -> pd.DataFrame:
    """One-liner CSV reader. See module docstring for full docs."""
    reader = MedicReader(sample_rows=sample_rows, confidence_threshold=confidence_threshold)
    kwargs: dict[str, Any] = {}
    if encoding is not None:
        kwargs["encoding"] = encoding
    if delimiter is not None:
        kwargs["delimiter"] = delimiter
    if na_values is not None:
        kwargs["na_values"] = na_values
    if preserve_strings is not None:
        kwargs["preserve_strings"] = preserve_strings
    if dayfirst is not None:
        kwargs["dayfirst"] = dayfirst
    if schema is not None:
        kwargs["schema"] = schema
    kwargs.update(pandas_kwargs)
    result = reader.read(filepath_or_buffer, **kwargs)
    return result


def read_raw(
    filepath_or_buffer: str | Path | IO[bytes],
    *,
    sample_rows: int = 1000,
) -> FileProfile:
    """Analyze without transforming. Returns FileProfile only. Phase 1: minimal implementation."""
    reader = MedicReader(sample_rows=sample_rows)
    df = reader.read(filepath_or_buffer)
    diagnosis = df.attrs.get("diagnosis")
    if diagnosis is None:
        raise ValueError("No diagnosis attached")
    profile: FileProfile = diagnosis.file_profile
    return profile
