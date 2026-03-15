"""csvmedic — Automatic locale-aware CSV reading."""

from csvmedic import accessor  # noqa: F401 — registers df.diagnosis accessor
from csvmedic._version import __version__
from csvmedic.batch import read_batch
from csvmedic.diagnosis import Diagnosis, TransformationRecord
from csvmedic.diff import DiffResult, diff
from csvmedic.models import ColumnProfile, FileProfile
from csvmedic.reader import MedicReader, read, read_raw
from csvmedic.schema import load_schema, save_schema, schema_path_for_csv

__all__ = [
    "__version__",
    "read",
    "read_raw",
    "read_batch",
    "MedicReader",
    "Diagnosis",
    "TransformationRecord",
    "ColumnProfile",
    "FileProfile",
    "save_schema",
    "load_schema",
    "schema_path_for_csv",
    "diff",
    "DiffResult",
]
