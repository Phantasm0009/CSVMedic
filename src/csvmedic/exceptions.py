"""Custom exceptions for csvmedic."""


class CsvMedicError(Exception):
    """Base exception for all csvmedic errors."""

    pass


class AmbiguousDateError(CsvMedicError):
    """Raised when date format cannot be disambiguated (e.g., DD/MM vs MM/DD)."""

    pass


class EncodingDetectionError(CsvMedicError):
    """Raised when encoding cannot be detected or decoding fails."""

    pass
