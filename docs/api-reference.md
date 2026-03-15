# API Reference

The main entry points are:

- **`csvmedic.read()`** — Read a CSV/Excel file into a DataFrame with automatic detection. Returns a `pd.DataFrame` with a `.diagnosis` attribute.
- **`csvmedic.read_raw()`** — Analyze a file and return a `FileProfile` without transforming.
- **`MedicReader`** — Stateful reader for repeated use with the same options.

See the docstrings in the source for full parameter lists:

- `csvmedic.read(filepath_or_buffer, *, encoding=..., delimiter=..., date_format=..., number_locale=..., dayfirst=..., preserve_strings=..., sample_rows=1000, confidence_threshold=0.75, na_values=..., **pandas_kwargs)`
- `csvmedic.read_raw(filepath_or_buffer, *, sample_rows=1000)`

## Data types

- **`FileProfile`** — Encoding, delimiter, row/column counts, and per-column `ColumnProfile` dict.
- **`ColumnProfile`** — Column name, detected type, confidence, action (converted/preserved/ambiguous/skipped/failed), and type-specific details.
- **`Diagnosis`** — File profile + list of transformation records + elapsed time. Attached to the DataFrame as `df.diagnosis`.
- **`TransformationRecord`** — Column, step name, before/after dtypes, rows affected/failed.

## Exceptions

- **`CsvMedicError`** — Base exception.
- **`AmbiguousDateError`** — Date format could not be disambiguated.
- **`EncodingDetectionError`** — Encoding could not be detected or decoding failed.
