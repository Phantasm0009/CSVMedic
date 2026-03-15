# csvmedic

[![PyPI](https://img.shields.io/pypi/v/csvmedic)](https://pypi.org/project/csvmedic/)
[![Python](https://img.shields.io/pypi/pyversions/csvmedic)](https://pypi.org/project/csvmedic/)
[![License](https://img.shields.io/pypi/l/csvmedic)](https://github.com/Phantasm0009/CSVMedic/blob/main/LICENSE)

Automatic locale-aware CSV and Excel reader. One line to clean messy data:

```python
import csvmedic

df = csvmedic.read("messy_file.csv")
print(df.diagnosis)  # See what was detected and converted
```

![csvmedic demo](docs/demo.gif)  
*Add a 30s terminal GIF here (see "Recording the demo GIF" below).*

## What it does

| Detects | Examples |
|--------|----------|
| **Encoding** | UTF-8, Windows-1252, ISO-8859-1, Shift-JIS, BOM |
| **Delimiter** | Comma, semicolon, tab, pipe |
| **Dates** | DD-MM vs MM-DD resolved statistically; ISO, European, US formats |
| **Numbers** | European (1.234,56) vs US (1,234.56); locale hint |
| **Booleans** | Yes/No, Ja/Nein, Oui/Non, Sí/No, and more |
| **Strings** | Preserves leading zeros (IDs like 00742) |

Every transformation is recorded in the `.diagnosis` attribute so you can audit what was changed.

## Installation

```bash
pip install csvmedic
```

Optional extras:

- `pip install csvmedic[fast]` — better dialect detection (clevercsv)
- `pip install csvmedic[excel]` — .xlsx support (openpyxl)
- `pip install csvmedic[all]` — both

## Configuration

Override auto-detection when you know better:

```python
df = csvmedic.read(
    "file.csv",
    encoding="utf-8",
    delimiter=";",
    dayfirst=True,              # Force DD-MM dates
    preserve_strings=["ID"],    # Never convert these columns
    sample_rows=2000,           # Rows to use for detection
    confidence_threshold=0.75,  # Min confidence to convert (0–1)
)
```

## Analyze without converting

```python
profile = csvmedic.read_raw("file.csv")
print(profile.summary())
print(profile.columns["Date"].details)
```

## Schema pinning (recurring files)

Save the detected schema after the first read and reuse it so the next read skips detection:

```python
df = csvmedic.read("monthly_export.csv")
csvmedic.save_schema(df.attrs["diagnosis"].file_profile, "monthly_export.csvmedic.json")

# Next time: same encoding, delimiter, and column types, no re-detection
df2 = csvmedic.read("monthly_export.csv", schema="monthly_export.csvmedic.json")
```

## Batch read with consensus

When reading many similar CSVs (e.g. one per month), use consensus so every file gets the same encoding and delimiter:

```python
dfs = csvmedic.read_batch(["jan.csv", "feb.csv", "mar.csv"], use_consensus=True)
# Encoding and delimiter are chosen by majority across the three files.
```

## Diff: pandas vs csvmedic

See exactly what pandas would have changed or corrupted vs what csvmedic preserves:

```python
result = csvmedic.diff("leading_zeros.csv")
print(result.summary())           # Columns/rows that differ
print(result.pandas_df)           # Default pandas read
print(result.csvmedic_df)         # csvmedic read (e.g. keeps "00742" as string)
print(result.sample_differences)  # Example (row, column, pandas_val, csvmedic_val)
```

## How disambiguation works

For ambiguous dates like `03/04/2025` (March 4 or April 3?), csvmedic uses the data itself: if any value has a day > 12 (e.g. `25/03/2025`), the column is treated as day-first. It also uses cross-column inference, separator hints (e.g. period = European), and sequential order. If it still can’t decide, the column stays as string and is marked ambiguous in the diagnosis.

## Recording the demo GIF

Record a ~30s terminal session for the README (e.g. with [asciinema](https://asciinema.org/) or [terminalizer](https://github.com/terminalizer/terminalizer)), then convert to GIF.

1. Install: `pip install csvmedic`
2. From the repo root (so `tests/fixtures/german_semicolon.csv` is reachable), copy the file:  
   `cp tests/fixtures/german_semicolon.csv .`
3. Record this session:

```bash
$ pip install csvmedic
$ python
>>> import csvmedic
>>> df = csvmedic.read("german_semicolon.csv")
>>> print(df.diagnosis)
```

Expected output (shape of the diagnosis):

```
csvmedic Diagnosis (0.08s)
  Encoding: windows-1252 (confidence: 95%)
  Delimiter: ';'
  Shape: 3 rows × 5 columns

  — Kunden-Nr: string (confidence: 100%, preserved)
      reason: leading_zeros_detected
  ✓ Datum: date (confidence: 97%, converted)
      format_detected: %d.%m.%Y
      dayfirst: True
  ✓ Umsatz: float (confidence: 95%, converted)
      locale_detected: de_DE
  ✓ Aktiv: boolean (confidence: 95%, converted)
>>> df.head()
```

4. Convert the recording to GIF (e.g. `asciinema cast → gif` or terminalizer’s GIF export).
5. Save as `docs/demo.gif` and commit. The README already references it above.

## Documentation

- [Quickstart](docs/quickstart.md)
- [How it works](docs/how-it-works.md)
- [API reference](docs/api-reference.md)
- [FAQ](docs/faq.md)

## License

MIT
