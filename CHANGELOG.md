# Changelog

## [0.1.0] - 2025-03-14

### Added

- Initial release
- `csvmedic.read()` — one-liner CSV reader with automatic encoding and delimiter detection (skeleton)
- `csvmedic.read_raw()` — analyze file without transforming
- `MedicReader` class for stateful configuration
- `Diagnosis` object attached to DataFrame via `df.attrs["diagnosis"]`
- `FileProfile` and `ColumnProfile` dataclasses for detection results
- Custom exceptions: `CsvMedicError`, `AmbiguousDateError`, `EncodingDetectionError`
