"""
Benchmark csvmedic.read() vs pd.read_csv() on a few files.
Run from project root: python benchmarks/bench_read.py
"""

from __future__ import annotations

import time
from pathlib import Path

def main() -> None:
    try:
        import pandas as pd
        import csvmedic
    except ImportError:
        print("Install pandas and csvmedic first.")
        return

    fixtures = Path(__file__).parent.parent / "tests" / "fixtures"
    if not fixtures.exists():
        print("No fixtures dir found.")
        return

    files = list(fixtures.glob("*.csv"))[:10]
    if not files:
        print("No CSV fixtures.")
        return

    print("| File | csvmedic (s) | pandas (s) |")
    print("|------|--------------|------------|")
    for path in files:
        try:
            t0 = time.perf_counter()
            df1 = csvmedic.read(path)
            t1 = time.perf_counter()
            t2 = time.perf_counter()
            df2 = pd.read_csv(path, dtype=str)
            t3 = time.perf_counter()
            print(f"| {path.name} | {t1-t0:.3f} | {t3-t2:.3f} |")
        except Exception as e:
            print(f"| {path.name} | error: {e} | - |")

if __name__ == "__main__":
    main()
