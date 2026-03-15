# CSVMEDIC — Cursor Build Document
## Comprehensive Technical Blueprint for AI-Assisted Development

---

## 1. PROJECT OVERVIEW

**csvmedic** is a Python library that provides a single-function interface for reading messy, locale-mangled CSV and Excel files into clean Pandas DataFrames. It automatically detects and resolves:

- **Delimiter ambiguity** (comma vs semicolon vs tab vs pipe)
- **Character encoding** (UTF-8, Windows-1252, ISO-8859-1, etc.)
- **Date format conflicts** — the core differentiator — using statistical column analysis to disambiguate DD-MM-YYYY vs MM-DD-YYYY
- **Number locale formatting** (European `1.234,56` vs US `1,234.56`)
- **String-that-looks-like-a-number preservation** (IDs with leading zeros like `00742`)
- **Boolean normalization** across locale variants (`Ja/Nein`, `Oui/Non`, `Yes/No`, `1/0`)

Every transformation is logged in a `.diagnosis` attribute so users can audit exactly what was changed.

**Primary use case:** `df = csvmedic.read("messy_file.csv")` — that's it.

**Key design principles:**
- Zero configuration required for the common case
- Every automatic decision can be overridden explicitly
- Never silently corrupt data — when ambiguous, preserve as string and flag in diagnosis
- Pure Python with minimal dependencies (pandas, chardet/charset-normalizer)
- Must be installable via `pip install csvmedic` and usable in one line

---

## 2. TECH STACK

### Core Library
- **Language:** Python 3.9+ (minimum version for modern type hints)
- **Type Hints:** Full PEP 484 type annotations on all public APIs
- **Data Backend:** pandas >= 1.5.0 (DataFrame is the return type)
- **Encoding Detection:** `charset-normalizer` (faster, more accurate than chardet, MIT licensed)
- **Date Parsing:** Custom statistical engine (NOT dateparser — too slow for column-level batch analysis)
- **CSV Dialect Detection:** `clevercsv` as optional accelerator, fallback to built-in `csv.Sniffer`

### Build & Package Tooling
- **Package Manager:** `uv` (modern, fast, Astral ecosystem)
- **Build Backend:** `hatchling` (via pyproject.toml, no setup.py)
- **Linting/Formatting:** `ruff` (single tool for both)
- **Type Checking:** `mypy` in strict mode
- **Testing:** `pytest` + `pytest-cov` (target 95%+ coverage)
- **CI:** GitHub Actions (lint → typecheck → test → publish)

### Documentation
- **Docs:** `mkdocs-material` with `mkdocstrings` for API reference
- **README:** Rich with code examples, badges, and comparison benchmarks

### Dependencies (in pyproject.toml)
```
[project]
dependencies = [
    "pandas>=1.5.0",
    "charset-normalizer>=3.0.0",
]

[project.optional-dependencies]
fast = ["clevercsv>=0.8.0"]       # Optional: better dialect detection
excel = ["openpyxl>=3.1.0"]       # Optional: .xlsx support
all = ["clevercsv>=0.8.0", "openpyxl>=3.1.0"]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.4.0",
    "mypy>=1.8",
    "pandas-stubs>=2.0",
    "mkdocs-material>=9.0",
    "mkdocstrings[python]>=0.24",
]
```

---

## 3. FOLDER & FILE STRUCTURE

```
csvmedic/
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint + typecheck + test on PR
│       └── publish.yml             # Publish to PyPI on tag
├── src/
│   └── csvmedic/
│       ├── __init__.py             # Public API: read(), read_raw(), __version__
│       ├── _version.py             # Single source of version string
│       ├── reader.py               # Main orchestrator: MedicReader class
│       ├── diagnosis.py            # Diagnosis dataclass + DiagnosisLog
│       ├── detectors/
│       │   ├── __init__.py
│       │   ├── encoding.py         # Encoding detection (charset-normalizer wrapper)
│       │   ├── dialect.py          # Delimiter + quoting detection
│       │   ├── dates.py            # Date format detection + disambiguation (CORE)
│       │   ├── numbers.py          # Number locale detection + normalization
│       │   ├── booleans.py         # Boolean variant detection + normalization
│       │   └── strings.py          # Leading-zero preservation, whitespace handling
│       ├── transformers/
│       │   ├── __init__.py
│       │   ├── date_transformer.py     # Apply detected date formats to columns
│       │   ├── number_transformer.py   # Apply number locale normalization
│       │   ├── boolean_transformer.py  # Normalize booleans to True/False
│       │   └── string_transformer.py   # Trim, preserve IDs, clean encoding artifacts
│       ├── models.py               # Pydantic-free dataclasses: ColumnProfile, FileProfile
│       ├── confidence.py           # Confidence scoring for ambiguous detections
│       └── exceptions.py           # Custom exceptions: AmbiguousDateError, etc.
├── tests/
│   ├── conftest.py                 # Shared fixtures: sample CSV generators
│   ├── fixtures/                   # Real-world test CSV files
│   │   ├── german_semicolon.csv
│   │   ├── french_dates.csv
│   │   ├── us_standard.csv
│   │   ├── mixed_dates_ambiguous.csv
│   │   ├── leading_zeros.csv
│   │   ├── european_numbers.csv
│   │   ├── multi_encoding.csv
│   │   ├── japanese_shift_jis.csv
│   │   ├── empty_file.csv
│   │   ├── single_column.csv
│   │   ├── huge_header.csv         # 200+ columns stress test
│   │   └── malformed_quotes.csv
│   ├── test_reader.py              # Integration tests for read()
│   ├── test_encoding_detector.py
│   ├── test_dialect_detector.py
│   ├── test_date_detector.py       # Most critical test file
│   ├── test_number_detector.py
│   ├── test_boolean_detector.py
│   ├── test_string_detector.py
│   ├── test_transformers.py
│   ├── test_diagnosis.py
│   └── test_confidence.py
├── benchmarks/
│   ├── bench_read.py               # Benchmark vs raw pandas on 100 files
│   └── sample_files/               # Diverse CSV collection for benchmarks
├── docs/
│   ├── index.md
│   ├── quickstart.md
│   ├── how-it-works.md             # Statistical date disambiguation explained
│   ├── api-reference.md
│   └── faq.md
├── pyproject.toml                  # Single config file for everything
├── README.md
├── LICENSE                         # MIT
├── CHANGELOG.md
└── .gitignore
```

---

## 4. DATABASE SCHEMA

**Not applicable for the open-source library (v1).** This is a pure Python package with no persistence layer.

For the future SaaS tier (csvmedic cloud), the schema would be:

```sql
-- Future SaaS schema (NOT part of v1 library build)
-- Included here for architectural awareness only

-- Users who sign up for the cloud UI
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free',  -- 'free', 'pro', 'enterprise'
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Each file upload and its diagnosis
CREATE TABLE file_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    original_filename TEXT NOT NULL,
    file_size_bytes INTEGER,
    encoding_detected TEXT,
    delimiter_detected TEXT,
    columns_analyzed INTEGER,
    rows_analyzed INTEGER,
    diagnosis_json JSONB NOT NULL,       -- Full Diagnosis object serialized
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Schema memory: remembers formats for recurring data sources
CREATE TABLE schema_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    profile_name TEXT NOT NULL,          -- e.g., "SAP exports" or "Client X monthly"
    column_rules JSONB NOT NULL,         -- Saved column format rules
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, profile_name)
);
```

---

## 5. CORE LOGIC & API ROUTES

### 5.1 — Public API (src/csvmedic/__init__.py)

```python
"""csvmedic — Automatic locale-aware CSV reading."""

from csvmedic._version import __version__
from csvmedic.reader import read, read_raw, MedicReader
from csvmedic.diagnosis import Diagnosis
from csvmedic.models import ColumnProfile, FileProfile

__all__ = [
    "__version__",
    "read",
    "read_raw",
    "MedicReader",
    "Diagnosis",
    "ColumnProfile",
    "FileProfile",
]
```

### 5.2 — Core Function Signatures

#### `read()` — The primary one-liner

```python
def read(
    filepath_or_buffer: str | Path | IO[bytes],
    *,
    # Override auto-detection when you know better:
    encoding: str | None = None,
    delimiter: str | None = None,
    date_format: str | dict[str, str] | None = None,
    number_locale: str | None = None,    # "en_US", "de_DE", "fr_FR", etc.
    dayfirst: bool | None = None,        # Force DD-MM if True, MM-DD if False
    preserve_strings: list[str] | None = None,  # Column names to never convert
    sample_rows: int = 1000,             # How many rows to analyze for detection
    confidence_threshold: float = 0.75,  # Below this, preserve as string
    na_values: list[str] | None = None,  # Additional NA markers
    # Pandas passthrough:
    **pandas_kwargs,                     # Any extra args forwarded to pd.read_csv
) -> pd.DataFrame:
    """
    Read a CSV/Excel file into a clean DataFrame with automatic
    locale detection and normalization.

    The returned DataFrame has a `.diagnosis` attribute containing
    a Diagnosis object with details of every transformation applied.

    Parameters
    ----------
    filepath_or_buffer : str, Path, or file-like
        Path to the CSV/TSV/Excel file, or a readable buffer.
    encoding : str, optional
        Force a specific encoding. If None, auto-detected.
    delimiter : str, optional
        Force a specific delimiter. If None, auto-detected.
    date_format : str or dict, optional
        Force date format(s). String applies to all date columns.
        Dict maps column names to format strings.
    number_locale : str, optional
        Force number locale (e.g., "de_DE" for European formatting).
    dayfirst : bool, optional
        If True, parse ambiguous dates as DD-MM. If False, MM-DD.
        If None (default), infer statistically per column.
    preserve_strings : list of str, optional
        Column names that should remain as strings (never converted).
    sample_rows : int, default 1000
        Number of rows to sample for type detection.
    confidence_threshold : float, default 0.75
        Minimum confidence (0-1) required to apply a type conversion.
        Below this threshold, the column is preserved as string.
    na_values : list of str, optional
        Additional strings to treat as NA/null.

    Returns
    -------
    pd.DataFrame
        Clean DataFrame with normalized types.
        Access `.diagnosis` attribute for transformation details.

    Examples
    --------
    >>> import csvmedic
    >>> df = csvmedic.read("german_export.csv")
    >>> print(df.diagnosis)
    FileProfile(encoding='windows-1252→utf-8', delimiter=';', ...)
    >>> print(df.diagnosis.columns['Datum'])
    ColumnProfile(original_type='string', detected='date',
                  format='DD.MM.YYYY', confidence=0.97, action='converted')
    """
```

#### `read_raw()` — Detection without transformation

```python
def read_raw(
    filepath_or_buffer: str | Path | IO[bytes],
    *,
    sample_rows: int = 1000,
) -> FileProfile:
    """
    Analyze a file and return detection results WITHOUT transforming it.
    Useful for previewing what csvmedic would do, or for building UIs.

    Returns
    -------
    FileProfile
        Complete analysis including encoding, delimiter, and per-column
        type detection with confidence scores.
    """
```

### 5.3 — Core Data Models (src/csvmedic/models.py)

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


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
    CONVERTED = "converted"         # Successfully converted
    PRESERVED = "preserved"         # Kept as string (by choice or low confidence)
    AMBIGUOUS = "ambiguous"         # Detected but confidence too low
    SKIPPED = "skipped"             # No conversion needed (already clean)
    FAILED = "failed"              # Conversion attempted but failed on some rows


@dataclass
class ColumnProfile:
    """Detection result for a single column."""
    name: str
    original_dtype: str                         # What pandas initially parsed it as
    detected_type: DetectedType                 # What csvmedic thinks it is
    confidence: float                           # 0.0 to 1.0
    action: Action                              # What was done
    details: dict = field(default_factory=dict) # Type-specific details

    # Date-specific details (when detected_type is DATE/DATETIME):
    #   details = {
    #       "format_detected": "DD.MM.YYYY",
    #       "dayfirst": True,
    #       "sample_values": ["01.03.2025", "15.07.2024"],
    #       "ambiguous_count": 3,      # values where day<=12 AND month<=12
    #       "unambiguous_count": 28,   # values where day>12 (confirms day-first)
    #       "parse_failures": 0,
    #   }

    # Number-specific details (when detected_type is FLOAT/INTEGER):
    #   details = {
    #       "locale_detected": "de_DE",
    #       "decimal_separator": ",",
    #       "thousands_separator": ".",
    #       "sample_values": ["1.234,56", "789,00"],
    #   }

    # Boolean-specific details:
    #   details = {
    #       "true_variants": ["Ja", "ja", "J"],
    #       "false_variants": ["Nein", "nein", "N"],
    #   }

    # String preservation details:
    #   details = {
    #       "reason": "leading_zeros_detected",
    #       "sample_values": ["00742", "00123"],
    #   }


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
    columns: dict[str, ColumnProfile]           # Column name -> profile
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dictionary (for JSON export)."""
        ...

    def summary(self) -> str:
        """Human-readable summary string."""
        ...
```

### 5.4 — Diagnosis Object (src/csvmedic/diagnosis.py)

```python
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
        for name, col in self.file_profile.columns.items():
            icon = {"converted": "✓", "preserved": "—", "ambiguous": "?",
                    "skipped": "·", "failed": "✗"}[col.action.value]
            lines.append(
                f"  {icon} {name}: {col.detected_type.value} "
                f"(confidence: {col.confidence:.0%}, {col.action.value})"
            )
            if col.details:
                for k, v in col.details.items():
                    if k != "sample_values":
                        lines.append(f"      {k}: {v}")
        return "\n".join(lines)


@dataclass
class TransformationRecord:
    """Log entry for a single transformation step."""
    column: str
    step: str           # e.g., "date_parse", "number_normalize", "bool_convert"
    before_dtype: str
    after_dtype: str
    rows_affected: int
    rows_failed: int
    details: str        # Human-readable description
```

### 5.5 — Date Detector: The Crown Jewel (src/csvmedic/detectors/dates.py)

This is the most important and algorithmically complex component.

```python
"""
Statistical date format detection and DD-MM vs MM-DD disambiguation.

ALGORITHM OVERVIEW
==================

For each string column, we:

1. PATTERN EXTRACTION
   - Sample up to `sample_rows` non-null values
   - Match against a library of date regex patterns:
     - ISO: YYYY-MM-DD, YYYY/MM/DD
     - European: DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY
     - US: MM/DD/YYYY, MM-DD-YYYY
     - Short: DD.MM.YY, MM/DD/YY, D/M/YYYY, M/D/YYYY
     - Named: "01 Jan 2025", "January 1, 2025", "1. März 2025"
     - Compact: YYYYMMDD, DDMMYYYY
   - If <50% of values match ANY date pattern, skip column.

2. FORMAT SCORING
   - For each candidate format, count how many values parse successfully.
   - The format with the highest parse rate wins initially.

3. AMBIGUITY DETECTION (the hard part)
   - If the top format is DD/MM or MM/DD and ALL values have both
     components <= 12 (e.g., 03/04/2025), the column is AMBIGUOUS.
   - Disambiguation strategies (applied in order):
     a. COLUMN SCAN: If ANY value in the full column has day > 12
        (e.g., 25/03/2025), the format is day-first.  If ANY value
        has month > 12 after swap, it's month-first. One unambiguous
        value resolves the entire column.
     b. CROSS-COLUMN INFERENCE: If another date column in the same
        file was unambiguously resolved, assume same locale.
     c. VALUE RANGE ANALYSIS: In day-first dates, the first component
        tends to have a wider range (1-31) vs month-first (1-12).
        Calculate the max of the first component. If max > 12,
        it must be day.
     d. SEQUENTIAL ANALYSIS: If dates appear to be sorted or
        sequential, test both orderings and see which produces a
        monotonic sequence.
     e. SEPARATOR HINT: Period separator (01.03.2025) is strongly
        associated with day-first European formats (German, Dutch,
        Finnish). Slash (01/03/2025) is ambiguous.
     f. GIVE UP GRACEFULLY: If confidence < threshold after all
        strategies, preserve as string and set action = AMBIGUOUS.

4. CONFIDENCE CALCULATION
   - Start at 1.0
   - Subtract 0.05 for each parse failure in the sample
   - Subtract 0.20 if all values were ambiguous (day<=12 AND month<=12)
   - Add back 0.15 for each disambiguation strategy that confirmed
   - Clamp to [0.0, 1.0]

IMPLEMENTATION NOTES
====================
- We NEVER use pandas' `infer_datetime_format` (deprecated and unreliable).
- We NEVER use dateutil.parser.parse on individual values (too slow, too
  permissive — it parses "hello" as a date sometimes).
- We use strptime with explicit format strings for speed.
- For named months ("Jan", "März", "Janvier"), we maintain a lookup
  table of month names in 15 common languages.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime


# Regex patterns ordered from most specific to least specific
DATE_PATTERNS: list[tuple[str, str, bool | None]] = [
    # (regex, strptime_format, dayfirst)
    # ISO 8601 — unambiguous
    (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "%Y-%m-%dT%H:%M:%S", None),
    (r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "%Y-%m-%d %H:%M:%S", None),
    (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d", None),

    # European with dots — strong day-first signal
    (r"\d{2}\.\d{2}\.\d{4}", "%d.%m.%Y", True),
    (r"\d{1,2}\.\d{1,2}\.\d{4}", "%d.%m.%Y", True),
    (r"\d{2}\.\d{2}\.\d{2}", "%d.%m.%y", True),

    # Slash-separated — AMBIGUOUS, needs disambiguation
    (r"\d{2}/\d{2}/\d{4}", None, None),   # Could be DD/MM or MM/DD
    (r"\d{1,2}/\d{1,2}/\d{4}", None, None),
    (r"\d{2}/\d{2}/\d{2}", None, None),

    # Dash-separated (non-ISO) — AMBIGUOUS
    (r"\d{2}-\d{2}-\d{4}", None, None),
    (r"\d{1,2}-\d{1,2}-\d{4}", None, None),

    # Compact
    (r"\d{8}", None, None),  # YYYYMMDD or DDMMYYYY — need analysis
]

# Month names in common languages for named-month parsing
MONTH_NAMES: dict[str, dict[str, int]] = {
    "en": {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
           "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
           "november": 11, "december": 12,
           "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
           "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12},
    "de": {"januar": 1, "februar": 2, "märz": 3, "april": 4, "mai": 5,
           "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10,
           "november": 11, "dezember": 12,
           "jan": 1, "feb": 2, "mär": 3, "apr": 4, "jun": 6,
           "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dez": 12},
    "fr": {"janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5,
           "juin": 6, "juillet": 7, "août": 8, "septembre": 9, "octobre": 10,
           "novembre": 11, "décembre": 12,
           "janv": 1, "févr": 2, "avr": 4, "juil": 7, "sept": 9,
           "oct": 10, "nov": 11, "déc": 12},
    "es": {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5,
           "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10,
           "noviembre": 11, "diciembre": 12},
    "nl": {"januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5,
           "juni": 6, "juli": 7, "augustus": 8, "september": 9, "oktober": 10,
           "november": 11, "december": 12},
    "pt": {"janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5,
           "junho": 6, "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10,
           "novembro": 11, "dezembro": 12},
    "it": {"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5,
           "giugno": 6, "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10,
           "novembre": 11, "dicembre": 12},
}


@dataclass
class DateDetectionResult:
    """Result of date detection for a single column."""
    is_date: bool
    format_string: str | None       # strptime format string
    dayfirst: bool | None           # None if unambiguous (ISO/named)
    confidence: float               # 0.0 to 1.0
    ambiguous_count: int            # Values where both day<=12 and month<=12
    unambiguous_count: int          # Values that resolved the ambiguity
    parse_success_rate: float       # Fraction of values that parsed
    disambiguation_method: str | None  # Which strategy resolved it
    sample_values: list[str]        # Representative values for diagnosis


def detect_date_column(
    values: list[str],
    column_name: str,
    other_column_dayfirst: bool | None = None,
) -> DateDetectionResult:
    """
    Analyze a list of string values and determine if they represent dates.

    Parameters
    ----------
    values : list of str
        Non-null string values from the column (already sampled).
    column_name : str
        Name of the column (used for heuristics — e.g., "date", "datum").
    other_column_dayfirst : bool or None
        If another date column in the same file was already resolved,
        pass its dayfirst value for cross-column inference.

    Returns
    -------
    DateDetectionResult
    """
    # Implementation steps:
    # 1. Filter empty/whitespace values
    # 2. Try each DATE_PATTERN regex
    # 3. For the best-matching pattern, attempt parsing
    # 4. If ambiguous, run disambiguation strategies
    # 5. Calculate confidence
    # 6. Return result
    ...


def _disambiguate_day_month(
    values: list[str],
    separator: str,
    other_column_dayfirst: bool | None,
) -> tuple[bool | None, float, str | None]:
    """
    Core disambiguation logic for DD/MM vs MM/DD.

    Returns (dayfirst, confidence_adjustment, method_used)
    """
    # Extract first and second numeric components
    first_components = []
    second_components = []
    for v in values:
        parts = re.split(r"[/\-.]", v)
        if len(parts) >= 2:
            try:
                first_components.append(int(parts[0]))
                second_components.append(int(parts[1]))
            except ValueError:
                continue

    # Strategy A: Any value with component > 12 resolves everything
    if any(f > 12 for f in first_components):
        return (True, 0.15, "unambiguous_day_value")   # Day-first confirmed
    if any(s > 12 for s in second_components):
        return (False, 0.15, "unambiguous_month_value") # Month-first confirmed

    # Strategy B: Cross-column inference
    if other_column_dayfirst is not None:
        return (other_column_dayfirst, 0.10, "cross_column_inference")

    # Strategy C: Value range analysis
    max_first = max(first_components) if first_components else 0
    max_second = max(second_components) if second_components else 0
    # (doesn't help if both max <= 12, but worth recording)

    # Strategy D: Separator heuristic
    if separator == ".":
        return (True, 0.08, "period_separator_european")

    # Strategy E: Sequential monotonicity test
    monotonic_df = _test_monotonicity(values, dayfirst=True)
    monotonic_mf = _test_monotonicity(values, dayfirst=False)
    if monotonic_df > monotonic_mf:
        return (True, 0.05, "sequential_analysis")
    if monotonic_mf > monotonic_df:
        return (False, 0.05, "sequential_analysis")

    # Give up — truly ambiguous
    return (None, -0.20, None)


def _test_monotonicity(values: list[str], dayfirst: bool) -> float:
    """Test how monotonic (sorted) the dates are under a given interpretation."""
    ...
```

### 5.6 — Number Locale Detector (src/csvmedic/detectors/numbers.py)

```python
"""
Detect number formatting locale (decimal and thousands separators).

KEY INSIGHT: The ambiguity is between:
  - US/UK:  "1,234.56"  (comma=thousands, period=decimal)
  - EU:     "1.234,56"  (period=thousands, comma=decimal)
  - Swiss:  "1'234.56"  (apostrophe=thousands, period=decimal)

ALGORITHM:
1. Count occurrences of . and , in numeric-looking strings.
2. If a string has both . and , — the LAST one is the decimal separator.
   "1,234.56" → decimal is "."
   "1.234,56" → decimal is ","
3. If a string has only one type, analyze position:
   - "1.234" could be 1234 (thousands) or 1.234 (decimal)
   - If digits after separator are exactly 3 → likely thousands
   - If digits after separator are 1-2 → likely decimal
4. Cross-validate across all values in the column for consistency.
"""

from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class NumberDetectionResult:
    """Result of number locale detection for a single column."""
    is_numeric: bool
    decimal_separator: str | None     # "." or "," or None
    thousands_separator: str | None   # ".", ",", "'", " ", or None
    locale_hint: str | None           # "en_US", "de_DE", "fr_FR", etc.
    confidence: float
    is_integer: bool                  # All values are whole numbers
    has_leading_zeros: bool           # Should be preserved as string
    sample_values: list[str]


def detect_number_column(values: list[str]) -> NumberDetectionResult:
    """
    Analyze a list of string values to detect number formatting.

    Returns NumberDetectionResult with detected locale information.
    """
    ...


def _classify_separators(value: str) -> tuple[str | None, str | None]:
    """
    For a single numeric string, determine decimal and thousands separators.

    Returns (decimal_separator, thousands_separator) or (None, None) if
    the value doesn't appear to be a formatted number.
    """
    # Remove currency symbols, whitespace, percent signs
    cleaned = re.sub(r"[€$£¥%\s]", "", value.strip())

    # Check for both separators present
    has_period = "." in cleaned
    has_comma = "," in cleaned
    has_apostrophe = "'" in cleaned

    if has_period and has_comma:
        # The last occurring separator is the decimal
        last_period = cleaned.rfind(".")
        last_comma = cleaned.rfind(",")
        if last_period > last_comma:
            return (".", ",")    # US: 1,234.56
        else:
            return (",", ".")    # EU: 1.234,56

    if has_period and not has_comma:
        # Analyze digits after the period
        after = cleaned.split(".")[-1]
        if len(after) == 3 and cleaned.count(".") == 1:
            # Ambiguous: could be "1.234" (thousands) or "1.234" (decimal)
            # Default: treat as decimal if only one period
            return (".", None)
        elif len(after) == 3 and cleaned.count(".") > 1:
            # "1.234.567" → periods are thousands separators
            return (None, ".")
        else:
            return (".", None)

    if has_comma and not has_period:
        after = cleaned.split(",")[-1]
        if len(after) == 3 and cleaned.count(",") == 1:
            return (None, ",")   # US thousands: "1,234"
        elif len(after) == 3 and cleaned.count(",") > 1:
            return (None, ",")   # "1,234,567"
        else:
            return (",", None)   # EU decimal: "3,14"

    return (None, None)
```

### 5.7 — Main Reader Orchestrator (src/csvmedic/reader.py)

```python
"""
Main orchestrator that ties all detectors and transformers together.

PIPELINE ORDER:
1. Detect encoding → decode file bytes to string
2. Detect dialect (delimiter, quoting, header)
3. Initial pandas read with string dtype (no type inference)
4. For each column, run detectors in order:
   a. String detector (leading zeros, whitespace)
   b. Boolean detector
   c. Number detector
   d. Date detector
5. Apply transformations based on detection results
6. Build Diagnosis object and attach to DataFrame
7. Return DataFrame

CRITICAL DESIGN DECISION: We read EVERYTHING as strings first
(dtype=str in pd.read_csv), then apply our own type inference.
This prevents pandas from silently corrupting data (e.g., converting
"00742" to 742, or "01/02/2025" to a wrong date).
"""

import time
from pathlib import Path
from typing import IO

import pandas as pd

from csvmedic.detectors.encoding import detect_encoding
from csvmedic.detectors.dialect import detect_dialect
from csvmedic.detectors.dates import detect_date_column
from csvmedic.detectors.numbers import detect_number_column
from csvmedic.detectors.booleans import detect_boolean_column
from csvmedic.detectors.strings import detect_string_preservation
from csvmedic.transformers.date_transformer import apply_date_conversion
from csvmedic.transformers.number_transformer import apply_number_conversion
from csvmedic.transformers.boolean_transformer import apply_boolean_conversion
from csvmedic.transformers.string_transformer import apply_string_cleaning
from csvmedic.diagnosis import Diagnosis, TransformationRecord
from csvmedic.models import FileProfile, ColumnProfile, DetectedType, Action


class MedicReader:
    """
    Stateful reader that can be configured and reused.
    The module-level `read()` function creates a temporary instance.
    """

    def __init__(
        self,
        sample_rows: int = 1000,
        confidence_threshold: float = 0.75,
    ):
        self.sample_rows = sample_rows
        self.confidence_threshold = confidence_threshold

    def read(
        self,
        filepath_or_buffer: str | Path | IO[bytes],
        **kwargs,
    ) -> pd.DataFrame:
        start_time = time.monotonic()
        transformations: list[TransformationRecord] = []

        # ---- STEP 1: Encoding Detection ----
        encoding = kwargs.pop("encoding", None)
        if encoding is None:
            enc_result = detect_encoding(filepath_or_buffer)
            encoding = enc_result.encoding
            enc_confidence = enc_result.confidence
        else:
            enc_confidence = 1.0

        # ---- STEP 2: Dialect Detection ----
        delimiter = kwargs.pop("delimiter", None)
        if delimiter is None:
            dialect_result = detect_dialect(filepath_or_buffer, encoding)
            delimiter = dialect_result.delimiter
            has_header = dialect_result.has_header
        else:
            has_header = True

        # ---- STEP 3: Initial Read (everything as string) ----
        df_raw = pd.read_csv(
            filepath_or_buffer,
            encoding=encoding,
            sep=delimiter,
            dtype=str,           # CRITICAL: prevent pandas auto-inference
            keep_default_na=True,
            na_values=kwargs.pop("na_values", None),
            header=0 if has_header else None,
            **kwargs.pop("pandas_kwargs", {}),
        )

        # ---- STEP 4: Per-Column Detection ----
        column_profiles: dict[str, ColumnProfile] = {}
        preserve_strings = kwargs.get("preserve_strings", []) or []
        force_dayfirst = kwargs.get("dayfirst", None)
        resolved_dayfirst: bool | None = None  # For cross-column inference

        for col_name in df_raw.columns:
            # Get non-null sample values
            sample = (
                df_raw[col_name]
                .dropna()
                .head(self.sample_rows)
                .astype(str)
                .tolist()
            )

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

            # 4a. Check for string preservation (leading zeros, etc.)
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

            # 4b. Check for booleans
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

            # 4c. Check for dates
            effective_dayfirst = force_dayfirst  # User override
            date_result = detect_date_column(
                sample,
                column_name=col_name,
                other_column_dayfirst=resolved_dayfirst if effective_dayfirst is None else None,
            )
            if date_result.is_date and date_result.confidence >= self.confidence_threshold:
                if effective_dayfirst is None:
                    effective_dayfirst = date_result.dayfirst
                if resolved_dayfirst is None and date_result.dayfirst is not None:
                    resolved_dayfirst = date_result.dayfirst  # For next columns
                column_profiles[col_name] = ColumnProfile(
                    name=col_name,
                    original_dtype="object",
                    detected_type=DetectedType.DATETIME if ":" in (date_result.format_string or "") else DetectedType.DATE,
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

            # 4d. Check for numbers
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
                        detected_type=DetectedType.INTEGER if num_result.is_integer else DetectedType.FLOAT,
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

            # Default: keep as string
            column_profiles[col_name] = ColumnProfile(
                name=col_name,
                original_dtype="object",
                detected_type=DetectedType.STRING,
                confidence=1.0,
                action=Action.SKIPPED,
            )

        # ---- STEP 5: Apply Transformations ----
        df = df_raw.copy()
        for col_name, profile in column_profiles.items():
            if profile.action != Action.CONVERTED:
                continue

            if profile.detected_type in (DetectedType.DATE, DetectedType.DATETIME):
                df, record = apply_date_conversion(
                    df, col_name, profile
                )
                transformations.append(record)

            elif profile.detected_type in (DetectedType.FLOAT, DetectedType.INTEGER):
                df, record = apply_number_conversion(
                    df, col_name, profile
                )
                transformations.append(record)

            elif profile.detected_type == DetectedType.BOOLEAN:
                df, record = apply_boolean_conversion(
                    df, col_name, profile
                )
                transformations.append(record)

        # ---- STEP 6: Build and Attach Diagnosis ----
        file_profile = FileProfile(
            filepath=str(filepath_or_buffer) if isinstance(filepath_or_buffer, (str, Path)) else None,
            encoding_detected=encoding,
            encoding_confidence=enc_confidence,
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

        # Attach diagnosis to DataFrame
        df.attrs["diagnosis"] = diagnosis

        # Also make it accessible as df.diagnosis via a property
        # (using pandas accessor registration)
        ...

        return df


# ---- Module-level convenience functions ----

def read(filepath_or_buffer, **kwargs) -> pd.DataFrame:
    """One-liner CSV reader. See MedicReader.read() for full docs."""
    reader_kwargs = {}
    for key in ("sample_rows", "confidence_threshold"):
        if key in kwargs:
            reader_kwargs[key] = kwargs.pop(key)
    reader = MedicReader(**reader_kwargs)
    return reader.read(filepath_or_buffer, **kwargs)


def read_raw(filepath_or_buffer, **kwargs) -> FileProfile:
    """Analyze without transforming. Returns FileProfile only."""
    ...
```

---

## 6. STEP-BY-STEP IMPLEMENTATION PLAN

### PHASE 1: Project Skeleton & Build System (Day 1-2)

**Goal:** A publishable (but empty) package on TestPyPI.

Steps:
1. Create the directory structure exactly as shown in Section 3.
2. Write `pyproject.toml` with all metadata, dependencies, and tool configs:
   - `[project]` section with name, version, description, authors, license, classifiers
   - `[build-system]` with hatchling
   - `[tool.ruff]` with line-length=99, target-version="py39"
   - `[tool.mypy]` with strict=true
   - `[tool.pytest.ini_options]` with testpaths, addopts="--cov"
3. Write `src/csvmedic/__init__.py` with version import and placeholder `read()` function.
4. Write `src/csvmedic/_version.py` with `__version__ = "0.1.0"`.
5. Write `src/csvmedic/exceptions.py` with `CsvMedicError`, `AmbiguousDateError`, `EncodingDetectionError`.
6. Write `src/csvmedic/models.py` with all dataclasses exactly as specified in Section 5.3.
7. Write `src/csvmedic/diagnosis.py` with the Diagnosis class and `__repr__` method as specified in Section 5.4.
8. Create `tests/conftest.py` with a fixture that generates simple test CSVs in a temp directory.
9. Write one test: `test_reader.py::test_read_simple_us_csv` that reads a basic US-format CSV and returns a DataFrame.
10. Verify: `uv run pytest` passes, `uv run ruff check src/` passes, `uv run mypy src/` passes.
11. Write `.github/workflows/ci.yml` — run lint, typecheck, test on push/PR.
12. Write initial `README.md` with the one-liner example code block.

**Deliverable:** `uv build` produces a `.whl` file. `pip install ./dist/csvmedic-0.1.0-py3-none-any.whl` works. `import csvmedic; csvmedic.read("test.csv")` runs (returns raw pandas output with empty diagnosis).

---

### PHASE 2: Encoding & Dialect Detection (Day 3-5)

**Goal:** csvmedic can correctly open any CSV regardless of encoding or delimiter.

Steps:
1. Write `src/csvmedic/detectors/encoding.py`:
   - Function `detect_encoding(filepath_or_buffer)` that returns `EncodingResult(encoding, confidence)`.
   - Use `charset_normalizer.from_path()` for file paths.
   - Use `charset_normalizer.from_bytes()` for buffers.
   - Handle BOM detection (UTF-8-BOM, UTF-16).
   - Add fallback chain: charset-normalizer → try UTF-8 → try Windows-1252.
2. Write `tests/test_encoding_detector.py`:
   - Test UTF-8, Windows-1252, ISO-8859-1, Shift-JIS files.
   - Test BOM handling.
   - Test empty file edge case.
3. Create test fixture files in `tests/fixtures/`:
   - `german_semicolon.csv` — Windows-1252 encoded, semicolon delimiter, German dates and numbers.
   - `french_dates.csv` — UTF-8, comma delimiter, DD/MM/YYYY dates.
   - `us_standard.csv` — UTF-8, comma delimiter, MM/DD/YYYY dates, US numbers.
   - `japanese_shift_jis.csv` — Shift-JIS encoded, comma delimiter.
4. Write `src/csvmedic/detectors/dialect.py`:
   - Function `detect_dialect(filepath_or_buffer, encoding)` that returns `DialectResult(delimiter, quotechar, has_header)`.
   - Try `clevercsv.Sniffer` first (if installed), fallback to `csv.Sniffer`.
   - Special handling for TSV (tab detection).
   - Header detection: use `csv.Sniffer().has_header()` + heuristic (first row all strings, second row has numbers).
5. Write `tests/test_dialect_detector.py`:
   - Test comma, semicolon, tab, pipe delimiters.
   - Test with and without headers.
   - Test quoted fields with delimiter inside quotes.
6. Update `reader.py` to use real encoding and dialect detection (replace placeholders from Phase 1).
7. Write integration test: `test_reader.py::test_read_german_semicolon` — reads `german_semicolon.csv`, verifies delimiter is `;` and encoding is `windows-1252`.

**Deliverable:** `csvmedic.read("any_encoding_any_delimiter.csv")` correctly reads the file into a DataFrame (all columns still strings — type detection comes next).

---

### PHASE 3: Date Detection & Disambiguation Engine (Day 6-12)

**Goal:** The core differentiator works — statistical date format detection with DD-MM vs MM-DD disambiguation.

Steps:
1. Write `src/csvmedic/detectors/dates.py` implementing the full algorithm from Section 5.5:
   - `detect_date_column()` — main entry point
   - `_match_date_patterns()` — try all regex patterns, return best match
   - `_disambiguate_day_month()` — the 5-strategy disambiguation engine
   - `_test_monotonicity()` — helper for sequential analysis
   - `_parse_named_month()` — handle "01 Jan 2025", "1. März 2025"
   - `_calculate_confidence()` — combine signals into 0-1 score
2. Write `tests/test_date_detector.py` — THIS IS THE MOST CRITICAL TEST FILE:
   - `test_iso_dates_unambiguous` — "2025-03-14" always works
   - `test_european_dot_dates` — "14.03.2025" detected as day-first
   - `test_us_slash_dates_unambiguous` — "03/25/2025" (day=25>12, so MM/DD)
   - `test_european_slash_dates_unambiguous` — "25/03/2025" (day=25>12, so DD/MM)
   - `test_ambiguous_all_low_values` — all values have day<=12 AND month<=12
   - `test_disambiguation_by_one_high_value` — column has one value "25/03/2025" among ambiguous ones
   - `test_disambiguation_cross_column` — second date column uses first column's resolution
   - `test_disambiguation_by_separator` — period separator → day-first
   - `test_disambiguation_sequential` — sorted dates resolve via monotonicity
   - `test_truly_ambiguous_stays_string` — when nothing resolves, preserve as string
   - `test_named_month_english` — "01 Jan 2025" parses correctly
   - `test_named_month_german` — "1. März 2025" parses correctly
   - `test_named_month_french` — "15 février 2025" parses correctly
   - `test_mixed_formats_in_column` — some ISO, some European → reject as ambiguous
   - `test_empty_column_not_date` — all nulls → not a date
   - `test_short_year_formats` — "14.03.25" detected correctly
   - `test_compact_yyyymmdd` — "20250314" parsed as YYYY-MM-DD
3. Write `src/csvmedic/transformers/date_transformer.py`:
   - `apply_date_conversion(df, col_name, profile)` → returns `(df, TransformationRecord)`
   - Uses `pd.to_datetime()` with the detected format string
   - Handles partial failures gracefully (coerce errors, count failures)
4. Write integration tests:
   - `test_reader.py::test_read_french_dates` — full pipeline, dates parsed correctly
   - `test_reader.py::test_read_mixed_date_columns` — file with 2 date columns, one unambiguous, one ambiguous → cross-column resolution works
5. Create fixture `tests/fixtures/mixed_dates_ambiguous.csv` with carefully crafted ambiguous dates.

**Deliverable:** `csvmedic.read("file_with_dates.csv")` correctly parses dates in any format. The `.diagnosis` shows which disambiguation strategy was used and the confidence score.

---

### PHASE 4: Number, Boolean & String Detectors (Day 13-17)

**Goal:** Complete type detection for all column types.

Steps:
1. Write `src/csvmedic/detectors/numbers.py` implementing the algorithm from Section 5.6:
   - `detect_number_column()` — main entry point
   - `_classify_separators()` — per-value separator analysis
   - `_consensus_locale()` — vote across all values for consistent locale
   - Handle edge cases: currency symbols, percentage signs, scientific notation
2. Write `tests/test_number_detector.py`:
   - `test_us_number_format` — "1,234.56" → decimal=".", thousands=","
   - `test_european_number_format` — "1.234,56" → decimal=",", thousands="."
   - `test_swiss_number_format` — "1'234.56"
   - `test_french_space_thousands` — "1 234,56"
   - `test_integer_with_thousands` — "1,234" → integer, thousands=","
   - `test_ambiguous_single_separator` — "1.234" (could be decimal or thousands)
   - `test_negative_numbers` — "-1.234,56"
   - `test_currency_symbols` — "€1.234,56", "$1,234.56"
   - `test_percentage` — "45,6%" (European)
3. Write `src/csvmedic/transformers/number_transformer.py`:
   - `apply_number_conversion(df, col_name, profile)` → `(df, TransformationRecord)`
   - Replace thousands separators, swap decimal separators, convert to float/int
4. Write `src/csvmedic/detectors/booleans.py`:
   - Detect `True/False`, `Yes/No`, `Y/N`, `1/0`, `Ja/Nein`, `Oui/Non`, `Sí/No`, `Vero/Falso`, `Waar/Onwaar`
   - Require >=90% of non-null values to match boolean patterns
5. Write `tests/test_boolean_detector.py`:
   - Test each language variant
   - Test mixed case
   - Test that columns with >2 unique values are NOT detected as boolean
6. Write `src/csvmedic/transformers/boolean_transformer.py`
7. Write `src/csvmedic/detectors/strings.py`:
   - Detect leading zeros (value starts with "0" and is all digits)
   - Detect columns that look numeric but should stay string (zip codes, phone numbers, product SKUs)
   - Heuristic: if >10% of values have leading zeros, preserve as string
8. Write `tests/test_string_detector.py`:
   - `test_leading_zeros_preserved` — "00742" stays as "00742"
   - `test_zip_codes_preserved` — "01234" stays as string
   - `test_phone_numbers_preserved` — "+1-555-0123" stays as string
9. Write `src/csvmedic/transformers/string_transformer.py`:
   - Strip whitespace
   - Fix encoding artifacts (Ã¤ → ä if detected as double-encoded)
10. Write full integration tests:
    - `test_reader.py::test_european_numbers_converted` — European CSV with numbers normalized
    - `test_reader.py::test_leading_zeros_preserved` — ID column stays string
    - `test_reader.py::test_booleans_german` — Ja/Nein → True/False
    - `test_reader.py::test_full_german_export` — the holy grail test: semicolons, Windows-1252, DD.MM.YYYY dates, European numbers, all in one file

**Deliverable:** `csvmedic.read()` handles every column type correctly. The `german_semicolon.csv` fixture processes end-to-end with perfect results.

---

### PHASE 5: Polish, Diagnosis UX & Publishing (Day 18-21)

**Goal:** Ship to PyPI with excellent documentation and developer experience.

Steps:
1. Implement `Diagnosis.__repr__()` for beautiful terminal output (as specified in Section 5.4).
2. Implement `FileProfile.to_dict()` for JSON serialization.
3. Implement `FileProfile.summary()` for one-line human-readable output.
4. Register a pandas accessor so `df.diagnosis` works as a property:
   ```python
   @pd.api.extensions.register_dataframe_accessor("diagnosis")
   class DiagnosisAccessor:
       def __init__(self, pandas_obj):
           self._obj = pandas_obj
       def __repr__(self):
           return repr(self._obj.attrs.get("diagnosis", "No diagnosis available"))
       # ... delegate all attribute access to the Diagnosis object
   ```
5. Implement `read_raw()` — calls the detection pipeline but skips transformation. Returns FileProfile only.
6. Add `confidence_threshold` enforcement:
   - If a column's detection confidence is below the threshold, preserve as string and set action=AMBIGUOUS.
   - Add a warning to `FileProfile.warnings`.
7. Write `tests/test_diagnosis.py`:
   - Test `__repr__` output format
   - Test `to_dict()` round-trip (serialize → deserialize)
   - Test that `df.diagnosis.columns["col_name"]` works
8. Write comprehensive `README.md`:
   - Hero code example (the one-liner)
   - "What it detects" section with table
   - "How disambiguation works" section with visual example
   - "Configuration" section showing all `read()` parameters
   - Benchmark comparison vs raw pandas
   - Installation instructions
   - Badge setup (PyPI version, Python version, CI status, coverage)
9. Write `docs/` for mkdocs-material:
   - `index.md` — overview + quickstart
   - `how-it-works.md` — deep dive into the date disambiguation algorithm
   - `api-reference.md` — auto-generated from docstrings
   - `faq.md` — common questions
10. Write `benchmarks/bench_read.py`:
    - Time `csvmedic.read()` vs `pd.read_csv()` on 10 diverse files
    - Output a markdown table of results
11. Set up `.github/workflows/publish.yml`:
    - Trigger on git tag push (v*)
    - Run full test suite
    - Build with `uv build`
    - Publish to PyPI with `uv publish` using trusted publishing (OIDC)
12. Create `CHANGELOG.md` for v0.1.0.
13. Final pre-publish checklist:
    - `uv run ruff check src/ tests/` — no errors
    - `uv run mypy src/` — no errors
    - `uv run pytest --cov=csvmedic --cov-report=term-missing` — 95%+ coverage
    - `uv build` — produces clean wheel
    - Test install in a fresh venv: `pip install dist/csvmedic-0.1.0*.whl`
    - Test the one-liner: `python -c "import csvmedic; print(csvmedic.__version__)"`
14. Publish: `git tag v0.1.0 && git push --tags`

**Deliverable:** `pip install csvmedic` works. The README on PyPI looks professional. The one-liner works on any messy CSV. `df.diagnosis` prints a beautiful terminal summary. Ready for the launch campaign.

---

## APPENDIX A: Test Fixture Specifications

### german_semicolon.csv (Windows-1252 encoded)
```
Kunden-Nr;Name;Datum;Umsatz;Aktiv
00742;Müller GmbH;01.03.2025;1.234,56;Ja
00123;Schäfer AG;15.07.2024;789,00;Nein
00456;Böhm & Co;25.12.2024;12.345,67;Ja
```

### french_dates.csv (UTF-8)
```
id,nom,date_inscription,montant
1,Dupont,15/02/2025,"1 234,56"
2,Martin,28/11/2024,"789,00"
3,Bernard,03/07/2024,"12 345,67"
```

### us_standard.csv (UTF-8)
```
id,name,signup_date,revenue,active
1,Smith Corp,03/15/2025,"1,234.56",Yes
2,Johnson LLC,07/28/2024,"789.00",No
3,Williams Inc,12/25/2024,"12,345.67",Yes
```

### mixed_dates_ambiguous.csv (UTF-8)
```
id,created_date,updated_date,amount
1,03/04/2025,05/06/2025,100.00
2,07/08/2025,09/10/2025,200.00
3,25/11/2025,13/12/2025,300.00
```
Note: Row 3 has day=25 and day=13, which resolves the ambiguity
for BOTH columns as day-first (DD/MM/YYYY).

### leading_zeros.csv (UTF-8)
```
product_id,zip_code,name,price
00742,01234,Widget A,19.99
00123,90210,Widget B,29.99
00456,00501,Widget C,9.99
```

### european_numbers.csv (UTF-8, semicolon)
```
Produkt;Preis;Menge;Gesamt
Widget A;19,99;100;1.999,00
Widget B;1.234,56;50;61.728,00
Widget C;0,99;1000;990,00
```

---

## APPENDIX B: Key Algorithmic Decisions & Rationale

1. **Why read as dtype=str first?**
   Pandas' default type inference silently corrupts data: "00742" becomes 742, "01/02/2025" might parse as Jan 2 or Feb 1 depending on locale settings. By reading everything as strings, we maintain full control.

2. **Why not use dateutil.parser?**
   It's too permissive (parses "hello" as today's date) and too slow for batch column analysis (it processes one string at a time with heavy heuristics). We use strptime with explicit formats, which is 50-100x faster.

3. **Why not use dateparser?**
   Same speed problem. dateparser is designed for single natural-language strings ("next Tuesday"), not for batch column analysis of structured date formats.

4. **Why statistical disambiguation instead of locale detection?**
   Locale detection (from column headers or file metadata) is unreliable. A German company might export data with English column names. Statistical analysis of the actual values is the only reliable signal.

5. **Why confidence thresholds?**
   Silent data corruption is worse than leaving data as strings. If we're only 60% sure a column is a date, it's better to leave it as a string and tell the user "I think this is a date but I'm not sure" than to silently convert 40% of values incorrectly.

6. **Why pandas accessor instead of DataFrame subclass?**
   Subclassing DataFrames is fragile — many pandas operations return a base DataFrame, losing the subclass. Using `attrs` + an accessor is the officially recommended approach and survives all standard operations.