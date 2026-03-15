"""
Schema pinning: save and load FileProfile as JSON for recurring files.

Use save_schema() after a read to cache the detected schema; use schema= in read()
to skip detection and apply the cached schema next time.
"""

from __future__ import annotations

import json
from pathlib import Path

from csvmedic.models import FileProfile


def save_schema(profile: FileProfile, path: str | Path) -> None:
    """Save a FileProfile to a JSON file for reuse (schema pinning)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile.to_dict(), f, indent=2)


def load_schema(path: str | Path) -> FileProfile:
    """Load a FileProfile from a JSON file (e.g. from a previous save_schema)."""
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return FileProfile.from_dict(data)


def schema_path_for_csv(csv_path: str | Path) -> Path:
    """Return the default schema path for a CSV: same directory, name.csvmedic.json."""
    p = Path(csv_path)
    return p.parent / f"{p.stem}.csvmedic.json"
