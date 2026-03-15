# How it works

## Statistical date disambiguation

The hardest part of locale-aware CSV reading is **DD-MM-YYYY vs MM-DD-YYYY**. A column like `03/04/2025` could be March 4 or April 3.

csvmedic does **not** rely on locale settings or column names. It uses the **data itself**:

1. **Unambiguous values** — If any value has a day > 12 (e.g. `25/03/2025`), the first number is the day → day-first (DD/MM).
2. **Cross-column inference** — If another date column in the same file was already resolved, assume the same order.
3. **Separator hint** — Period (e.g. `01.03.2025`) is strongly associated with European day-first formats.
4. **Sequential analysis** — If dates are sorted, try both orderings and see which gives a monotonic sequence.
5. **Otherwise** — Preserve as string and mark as ambiguous in the diagnosis.

So one unambiguous value (e.g. `25/03/2025`) in a column can resolve the entire column.

## Pipeline order

1. Detect encoding (charset-normalizer, BOM, fallbacks).
2. Detect dialect (delimiter, quoting, header).
3. Read with `dtype=str` so pandas does not corrupt data.
4. For each column: string preservation → boolean → date → number → default string.
5. Apply conversions and attach the diagnosis.

## Confidence threshold

By default, a type is applied only if confidence ≥ 0.75. Otherwise the column stays as string and is marked ambiguous. You can change this with `confidence_threshold=0.8` (stricter) or `0.6` (more permissive).
