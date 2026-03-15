"""
Multi-file batch read with consensus detection.

When reading multiple similar CSVs (e.g. monthly exports), run encoding and
delimiter detection on each file's sample and use the majority result for all,
so every file is read with the same settings.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from csvmedic.detectors.dialect import detect_dialect
from csvmedic.detectors.encoding import detect_encoding
from csvmedic.reader import _read_byte_sample, read


def _consensus_encoding_dialect(
    paths: list[Path],
) -> tuple[str, str, bool]:
    """Detect encoding/dialect per path; return (encoding, delimiter, has_header)."""
    encodings: list[str] = []
    delimiters: list[str] = []
    headers: list[bool] = []
    for path in paths:
        try:
            bytes_sample, _ = _read_byte_sample(path)
            enc = detect_encoding(bytes_sample)
            encodings.append(enc.encoding)
            decoded = bytes_sample.decode(enc.encoding, errors="replace")
            dialect = detect_dialect(None, enc.encoding, sample_text=decoded)
            delimiters.append(dialect.delimiter)
            headers.append(dialect.has_header)
        except Exception:
            continue
    if not encodings:
        return ("utf-8", ",", True)
    enc_counter = Counter(encodings)
    delim_counter = Counter(delimiters)
    encoding = enc_counter.most_common(1)[0][0]
    delimiter = delim_counter.most_common(1)[0][0]
    has_header = sum(headers) > len(headers) / 2
    return (encoding, delimiter, has_header)


def read_batch(
    paths: str | Path | list[str] | list[Path],
    *,
    encoding: str | None = None,
    delimiter: str | None = None,
    use_consensus: bool = True,
    **read_kw: Any,
) -> list[pd.DataFrame]:
    """
    Read multiple CSV files with optional consensus detection.

    When use_consensus is True (default), encoding and delimiter are detected
    on a sample from each file and the majority choice is used for every file,
    so all DataFrames are read with the same settings. When use_consensus is
    False or encoding/delimiter are provided, each file is read with read() and
    its own detection (or the given overrides).

    Parameters
    ----------
    paths : path or list of paths
        One or more paths to CSV files.
    encoding : str, optional
        If set, overrides consensus and is used for all files.
    delimiter : str, optional
        If set, overrides consensus and is used for all files.
    use_consensus : bool
        If True, run detection on each file and use majority encoding/delimiter.
    **read_kw
        Passed through to read() (e.g. sample_rows, confidence_threshold).

    Returns
    -------
    list of DataFrame
        One DataFrame per path, in order.
    """
    if isinstance(paths, (str, Path)):
        paths = [Path(paths)]
    else:
        paths = [Path(p) for p in paths]
    if not paths:
        return []

    if use_consensus and encoding is None and delimiter is None:
        enc, delim, has_header = _consensus_encoding_dialect(paths)
        # Pass consensus to read(); has_header is not a read() kwarg so we rely on detection
        read_kw["encoding"] = enc
        read_kw["delimiter"] = delim
    elif encoding is not None:
        read_kw["encoding"] = encoding
    if delimiter is not None:
        read_kw["delimiter"] = delimiter

    return [read(p, **read_kw) for p in paths]
