"""
Delimiter and quoting detection with optional clevercsv and csv.Sniffer fallback.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import IO


def _read_sample_text(
    filepath_or_buffer: str | Path | IO[bytes],
    encoding: str,
    sample_size: int = 65536,
) -> str:
    """Read a sample of the file as decoded text."""
    if isinstance(filepath_or_buffer, (str, Path)):
        path = Path(filepath_or_buffer)
        with open(path, encoding=encoding, errors="replace") as f:
            return f.read(sample_size)
    # buffer: assume it might need reset
    raw = filepath_or_buffer.read(sample_size)
    if hasattr(filepath_or_buffer, "seek"):
        filepath_or_buffer.seek(0)
    if isinstance(raw, bytes):
        return raw.decode(encoding, errors="replace")
    return raw


def detect_dialect(
    filepath_or_buffer: str | Path | IO[bytes] | None,
    encoding: str,
    *,
    sample_text: str | None = None,
) -> DialectResult:
    """
    Detect CSV dialect (delimiter, quote char, has_header).

    Tries clevercsv.Sniffer if installed, otherwise csv.Sniffer.
    TSV (tab) is detected explicitly when no comma/semicolon fits.

    Parameters
    ----------
    filepath_or_buffer : str, Path, file-like, or None
        Path or open buffer. Can be None if sample_text is provided.
    encoding : str
        Encoding to use when reading from path or bytes buffer.
    sample_text : str, optional
        Pre-decoded text to use instead of reading from filepath_or_buffer (avoids 2nd I/O).

    Returns
    -------
    DialectResult
    """
    if sample_text is not None:
        sample = sample_text
    elif filepath_or_buffer is not None:
        sample = _read_sample_text(filepath_or_buffer, encoding)
    else:
        sample = ""

    if not sample.strip():
        return DialectResult(delimiter=",", quotechar='"', has_header=True)

    # Optional: clevercsv for better dialect detection
    try:
        import clevercsv  # type: ignore[import-not-found]

        dialect = clevercsv.Sniffer().sniff(sample)
        return DialectResult(
            delimiter=dialect.delimiter,
            quotechar=getattr(dialect, "quotechar", None) or '"',
            has_header=_detect_has_header(sample, dialect.delimiter, encoding),
        )
    except ImportError:
        pass
    except Exception:
        pass

    # Explicit tab check (TSV)
    first_line = sample.split("\n")[0] if "\n" in sample else sample
    if "\t" in first_line and "," not in first_line and ";" not in first_line:
        return DialectResult(
            delimiter="\t",
            quotechar='"',
            has_header=_detect_has_header(sample, "\t", encoding),
        )

    # Standard library csv.Sniffer
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample, delimiters=",;\t|")
        has_header = sniffer.has_header(sample)
    except csv.Error:
        # Fallback: count delimiters in first two lines
        lines = [ln for ln in sample.splitlines()[:3] if ln.strip()]
        if len(lines) < 2:
            has_header = True
        else:
            has_header = _heuristic_has_header(lines[0], lines[1])
        dialect = None

    if dialect is not None:
        return DialectResult(
            delimiter=dialect.delimiter,
            quotechar=dialect.quotechar or '"',
            has_header=has_header,
        )

    # Last resort: comma
    return DialectResult(
        delimiter=",",
        quotechar='"',
        has_header=_heuristic_has_header(
            lines[0] if lines else "",
            lines[1] if len(lines) > 1 else "",
        ),
    )


def _heuristic_has_header(first_line: str, second_line: str) -> bool:
    """Heuristic: first row all strings, second row has numbers -> header."""
    first_parts = first_line.split(",")
    second_parts = second_line.split(",")
    if len(first_parts) != len(second_parts):
        return True

    # If second line has more numbers, likely first is header
    def looks_numeric(s: str) -> bool:
        s = s.strip().strip('"').strip()
        if not s:
            return False
        try:
            float(s.replace(",", "").replace(" ", ""))
            return True
        except ValueError:
            return False

    second_numeric = sum(1 for p in second_parts if looks_numeric(p))
    first_numeric = sum(1 for p in first_parts if looks_numeric(p))
    return second_numeric > first_numeric or (first_numeric == 0 and second_numeric == 0)


def _detect_has_header(sample: str, delimiter: str, encoding: str) -> bool:
    """Use csv.Sniffer.has_header when possible."""
    try:
        sniffer = csv.Sniffer()
        return sniffer.has_header(sample)
    except csv.Error:
        lines = [ln for ln in sample.splitlines()[:3] if ln.strip()]
        if len(lines) >= 2:
            return _heuristic_has_header(lines[0], lines[1])
        return True


class DialectResult:
    """Result of dialect detection."""

    __slots__ = ("delimiter", "quotechar", "has_header")

    def __init__(self, delimiter: str, quotechar: str, has_header: bool) -> None:
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.has_header = has_header
