"""
Encoding detection using charset-normalizer with BOM handling and fallback chain.
"""

from __future__ import annotations

from pathlib import Path
from typing import IO

from csvmedic.exceptions import EncodingDetectionError

# Default sample size for encoding detection (avoid loading multi-GB files into RAM).
DEFAULT_ENCODING_SAMPLE_BYTES = 512 * 1024  # 512 KiB


def _get_bytes(
    filepath_or_buffer: str | Path | IO[bytes] | bytes,
    sample_size: int | None = None,
) -> bytes:
    """Read raw bytes from path or buffer. If sample_size is set, read at most that many bytes."""
    if isinstance(filepath_or_buffer, bytes):
        if sample_size is not None and len(filepath_or_buffer) > sample_size:
            return filepath_or_buffer[:sample_size]
        return filepath_or_buffer
    if isinstance(filepath_or_buffer, (str, Path)):
        path = Path(filepath_or_buffer)
        if not path.exists():
            raise EncodingDetectionError(f"File not found: {path}")
        with open(path, "rb") as f:
            return f.read(sample_size) if sample_size else f.read()
    # file-like
    raw = filepath_or_buffer.read(sample_size) if sample_size else filepath_or_buffer.read()
    if isinstance(raw, str):
        return raw.encode("utf-8")
    return raw


def detect_encoding(
    filepath_or_buffer: str | Path | IO[bytes] | bytes,
    sample_size: int | None = DEFAULT_ENCODING_SAMPLE_BYTES,
) -> EncodingResult:
    """
    Detect encoding of a CSV file or buffer.

    Uses charset-normalizer, then BOM detection, then fallback chain:
    UTF-8 -> Windows-1252.

    Returns
    -------
    EncodingResult
        encoding : str
            Detected encoding name (e.g. "utf-8", "windows-1252").
        confidence : float
            Confidence score 0.0 to 1.0.
    """
    # When input is already bytes, use it all; otherwise cap read to sample_size.
    read_size = None if isinstance(filepath_or_buffer, bytes) else sample_size
    try:
        raw = _get_bytes(filepath_or_buffer, read_size)
    except OSError as e:
        raise EncodingDetectionError(f"Cannot read file: {e}") from e

    if not raw:
        return EncodingResult(encoding="utf-8", confidence=0.0)

    # BOM detection
    if raw.startswith(b"\xef\xbb\xbf"):
        return EncodingResult(encoding="utf-8-sig", confidence=1.0)
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return EncodingResult(encoding="utf-16", confidence=1.0)

    # charset-normalizer
    try:
        from charset_normalizer import from_bytes

        results = from_bytes(raw)
        if results:
            best = results.best()
            if best is not None:
                encoding = best.encoding or "utf-8"
                # ASCII is a subset of UTF-8; report as utf-8 for consistency
                if encoding and encoding.lower() in ("ascii", "ascii_8_bit"):
                    encoding = "utf-8"
                # CharsetMatch: use coherence (higher = more confident) or 1 - chaos
                conf = getattr(best, "coherence", None)
                if conf is not None and float(conf) > 0:
                    confidence = float(conf)
                else:
                    chaos = getattr(best, "chaos", 0.2)
                    confidence = 1.0 - float(chaos)
                # Ensure a minimum confidence when we got a clear encoding from the detector
                confidence = max(0.5, min(1.0, confidence))
                return EncodingResult(encoding=encoding, confidence=confidence)
    except ImportError:
        pass

    # Fallback: try UTF-8
    try:
        raw.decode("utf-8")
        return EncodingResult(encoding="utf-8", confidence=0.7)
    except UnicodeDecodeError:
        pass

    # Fallback: Windows-1252 (common for European exports)
    try:
        raw.decode("cp1252")
        return EncodingResult(encoding="windows-1252", confidence=0.6)
    except UnicodeDecodeError:
        pass

    return EncodingResult(encoding="utf-8", confidence=0.0)


class EncodingResult:
    """Result of encoding detection."""

    __slots__ = ("encoding", "confidence")

    def __init__(self, encoding: str, confidence: float) -> None:
        self.encoding = encoding
        self.confidence = confidence
