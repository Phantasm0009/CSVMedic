# csvmedic

**Automatic locale-aware CSV and Excel reading.** One line to clean messy data:

```python
import csvmedic

df = csvmedic.read("messy_file.csv")
print(df.diagnosis)  # See what was detected and converted
```

## What it detects

| Problem | Solution |
|--------|----------|
| Wrong encoding | UTF-8, Windows-1252, ISO-8859-1, Shift-JIS, etc. |
| Wrong delimiter | Comma, semicolon, tab, pipe |
| Date ambiguity | DD-MM vs MM-DD resolved statistically |
| Number locale | European (1.234,56) vs US (1,234.56) |
| Booleans | Yes/No, Ja/Nein, Oui/Non, and more |
| Leading zeros | IDs like 00742 preserved as string |

## Quick start

See [Quickstart](quickstart.md). For how date disambiguation works, see [How it works](how-it-works.md).
