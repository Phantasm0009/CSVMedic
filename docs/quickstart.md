# Quickstart

## Installation

```bash
pip install csvmedic
```

## Basic usage

```python
import csvmedic

# One line — encoding, delimiter, and types are detected automatically
df = csvmedic.read("german_export.csv")

# Inspect what was done
print(df.diagnosis)
# csvmedic Diagnosis (0.12s)
#   Encoding: windows-1252 (confidence: 95%)
#   Delimiter: ';'
#   Shape: 1000 rows × 5 columns
#   ✓ Kunden-Nr: string (preserved, leading zeros)
#   ✓ Datum: date (converted, DD.MM.YYYY)
#   ...
```

## Analyze without converting

Use `read_raw()` to get detection results without transforming the file:

```python
profile = csvmedic.read_raw("file.csv")
print(profile.summary())
print(profile.columns["Date"].details)
```

## Override detection

When you know better, pass explicit options:

```python
df = csvmedic.read(
    "file.csv",
    encoding="utf-8",
    delimiter=";",
    dayfirst=True,           # Force DD-MM dates
    preserve_strings=["ID"], # Never convert this column
)
```
