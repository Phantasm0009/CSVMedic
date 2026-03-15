# csvmedic

[![PyPI](https://img.shields.io/pypi/v/csvmedic)](https://pypi.org/project/csvmedic/)
[![Python](https://img.shields.io/pypi/pyversions/csvmedic)](https://pypi.org/project/csvmedic/)
[![License](https://img.shields.io/pypi/l/csvmedic)](https://github.com/Phantasm0009/CSVMedic/blob/main/LICENSE)

One-line CSV reading that auto-detects encoding, delimiter, dates, number formats, and booleans—so you don’t lose leading zeros or misinterpret 03/04/2025.

```python
import csvmedic

df = csvmedic.read("export.csv")
print(df.diagnosis)  # What was detected and converted
```

![csvmedic demo](docs/demo.gif)

## Features

| Detects | Examples |
|--------|----------|
| **Encoding** | UTF-8, Windows-1252, ISO-8859-1, Shift-JIS, BOM |
| **Delimiter** | Comma, semicolon, tab, pipe |
| **Dates** | DD-MM vs MM-DD resolved from data; ISO, European, US formats |
| **Numbers** | European (1.234,56) vs US (1,234.56) |
| **Booleans** | Yes/No, Ja/Nein, Oui/Non, Sí/No, and more |
| **Strings** | Preserves leading zeros (e.g. IDs 00742) |

All decisions are recorded on the returned DataFrame’s `.diagnosis` attribute.

## Installation

```bash
pip install csvmedic
```

Optional extras:

- `csvmedic[fast]` — better dialect detection (clevercsv)
- `csvmedic[excel]` — .xlsx support (openpyxl)
- `csvmedic[all]` — both

## Usage

**Override detection when you know better:**

```python
df = csvmedic.read(
    "file.csv",
    encoding="utf-8",
    delimiter=";",
    dayfirst=True,
    preserve_strings=["ID"],
    confidence_threshold=0.75,
)
```

**Inspect without converting:**

```python
profile = csvmedic.read_raw("file.csv")
print(profile.summary())
```

**Schema pinning (recurring files):**

```python
df = csvmedic.read("monthly_export.csv")
csvmedic.save_schema(df.attrs["diagnosis"].file_profile, "monthly_export.csvmedic.json")
# Next run: skip detection
df2 = csvmedic.read("monthly_export.csv", schema="monthly_export.csvmedic.json")
```

**Batch with consensus:**

```python
dfs = csvmedic.read_batch(["jan.csv", "feb.csv", "mar.csv"], use_consensus=True)
```

**Compare with pandas:**

```python
result = csvmedic.diff("file.csv")
print(result.summary())
# result.pandas_df, result.csvmedic_df, result.sample_differences
```

## Date disambiguation

For ambiguous values like `03/04/2025`, csvmedic uses the column: if any value has day > 12 (e.g. `25/03/2025`), the column is treated as day-first. It also uses cross-column inference, separator hints (e.g. period → European), and order. If still ambiguous, the column stays as string and is marked in the diagnosis.

## Documentation

- [Quickstart](docs/quickstart.md)
- [How it works](docs/how-it-works.md)
- [API reference](docs/api-reference.md)
- [FAQ](docs/faq.md)

## License

MIT
