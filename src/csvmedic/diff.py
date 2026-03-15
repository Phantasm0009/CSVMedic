"""
Diff diagnostic: compare pandas default read vs csvmedic read.

Shows what pandas would have corrupted (e.g. leading zeros, wrong dates)
vs what csvmedic preserved or fixed. Use for README screenshots and audits.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any

import pandas as pd

from csvmedic.reader import read


@dataclass
class DiffResult:
    """Result of comparing pandas vs csvmedic on the same file."""

    filepath: str | None
    pandas_df: pd.DataFrame
    csvmedic_df: pd.DataFrame
    columns_with_differences: list[str] = field(default_factory=list)
    row_count_difference: bool = False
    column_count_difference: bool = False
    sample_differences: list[tuple[int, str, object, object]] = field(default_factory=list)
    max_sample_rows: int = 5

    def summary(self) -> str:
        """Human-readable summary for terminal or logs."""
        lines = [
            "csvmedic.diff() — pandas vs csvmedic",
            f"  File: {self.filepath or '(buffer)'}",
            f"  Shape: pandas {self.pandas_df.shape} vs csvmedic {self.csvmedic_df.shape}",
        ]
        if self.row_count_difference or self.column_count_difference:
            lines.append("  ⚠ Row or column count differs (pandas may have misparsed).")
        if self.columns_with_differences:
            lines.append(
                f"  Columns with value differences: {self.columns_with_differences}"
            )
            if self.sample_differences:
                lines.append("  Sample value differences (row, column, pandas, csvmedic):")
                for row_idx, col, pval, cval in self.sample_differences[: self.max_sample_rows]:
                    lines.append(f"    ({row_idx}, {col!r}): {pval!r} vs {cval!r}")
        elif not (self.row_count_difference or self.column_count_difference):
            lines.append("  No differences (same shape and no per-cell differences).")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return self.summary()


def _find_differences(
    pdf: pd.DataFrame,
    cdf: pd.DataFrame,
    max_sample: int = 5,
) -> tuple[list[str], list[tuple[int, str, object, object]]]:
    """Compare the two DataFrames; return (columns_with_diffs, sample_tuples)."""
    cols_with_diffs: list[str] = []
    sample: list[tuple[int, str, object, object]] = []
    common_cols = [c for c in pdf.columns if c in cdf.columns]
    for col in common_cols:
        pser = pdf[col]
        cser = cdf[col]
        if len(pser) != len(cser):
            cols_with_diffs.append(col)
            continue
        for i in range(len(pser)):
            pval = pser.iloc[i]
            cval = cser.iloc[i]
            if pd.isna(pval) and pd.isna(cval):
                continue
            if pd.isna(pval) or pd.isna(cval) or pval != cval:
                if col not in cols_with_diffs:
                    cols_with_diffs.append(col)
                if len(sample) < max_sample:
                    sample.append((i, col, pval, cval))
    return (cols_with_diffs, sample)


def diff(
    filepath_or_buffer: str | Path | IO[bytes],
    **read_kw: Any,
) -> DiffResult:
    """
    Compare pandas default read vs csvmedic read on the same file.

    Reads the file twice: once with pd.read_csv() (default inference, which
    can strip leading zeros, misinterpret dates, etc.) and once with
    csvmedic.read(). Returns a DiffResult with both DataFrames and a summary
    of which columns and rows differ.

    Use for audits, README screenshots, and proving value to stakeholders.

    Parameters
    ----------
    filepath_or_buffer : path or buffer
        CSV file to compare.
    **read_kw
        Passed to csvmedic.read() (e.g. encoding, delimiter). Not used for
        the pandas read (pandas uses its own defaults).

    Returns
    -------
    DiffResult
        .pandas_df, .csvmedic_df, .columns_with_differences, .sample_differences, .summary().
    """
    path_str: str | None = None
    if isinstance(filepath_or_buffer, (str, Path)):
        path_str = str(filepath_or_buffer)
        path = Path(filepath_or_buffer)
        pandas_df = pd.read_csv(path)
        csvmedic_df = read(path, **read_kw)
    else:
        # Buffer: read once, then give each reader a fresh copy so neither exhausts it
        raw = filepath_or_buffer.read()
        if isinstance(raw, str):
            raw_bytes = raw.encode("utf-8")
        else:
            raw_bytes = raw
        pandas_df = pd.read_csv(io.BytesIO(raw_bytes))
        csvmedic_df = read(io.BytesIO(raw_bytes), **read_kw)

    row_diff = len(pandas_df) != len(csvmedic_df)
    col_diff = list(pandas_df.columns) != list(csvmedic_df.columns) or len(
        pandas_df.columns
    ) != len(csvmedic_df.columns)
    cols_with_diffs, sample_diffs = _find_differences(
        pandas_df, csvmedic_df, max_sample=5
    )

    return DiffResult(
        filepath=path_str,
        pandas_df=pandas_df,
        csvmedic_df=csvmedic_df,
        columns_with_differences=cols_with_diffs,
        row_count_difference=row_diff,
        column_count_difference=col_diff,
        sample_differences=sample_diffs,
        max_sample_rows=5,
    )
