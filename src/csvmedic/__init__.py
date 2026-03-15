"""csvmedic — Automatic locale-aware CSV reading."""

from csvmedic import accessor  # noqa: F401 — registers df.diagnosis accessor
from csvmedic._version import __version__
from csvmedic.diagnosis import Diagnosis, TransformationRecord
from csvmedic.models import ColumnProfile, FileProfile
from csvmedic.reader import MedicReader, read, read_raw

__all__ = [
    "__version__",
    "read",
    "read_raw",
    "MedicReader",
    "Diagnosis",
    "TransformationRecord",
    "ColumnProfile",
    "FileProfile",
]
