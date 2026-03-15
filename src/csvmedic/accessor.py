"""Pandas DataFrame accessor for .diagnosis attribute."""

from __future__ import annotations

from typing import Any

import pandas as pd


@pd.api.extensions.register_dataframe_accessor("diagnosis")
class DiagnosisAccessor:
    """Accessor for df.diagnosis — returns the Diagnosis object from df.attrs."""

    def __init__(self, pandas_obj: pd.DataFrame) -> None:
        self._obj = pandas_obj

    def __repr__(self) -> str:
        d = self._obj.attrs.get("diagnosis")
        if d is None:
            return "No diagnosis available"
        return repr(d)

    def __getattr__(self, name: str) -> Any:
        d = self._obj.attrs.get("diagnosis")
        if d is None:
            raise AttributeError("No diagnosis available")
        return getattr(d, name)
