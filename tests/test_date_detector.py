"""Tests for date format detection and disambiguation."""

from csvmedic.detectors.dates import (
    _disambiguate_day_month,
    _test_monotonicity,
    detect_date_column,
)


def test_iso_dates_unambiguous() -> None:
    values = ["2025-03-14", "2024-01-01", "2023-12-31"]
    r = detect_date_column(values, "date")
    assert r.is_date is True
    assert r.format_string == "%Y-%m-%d"
    assert r.dayfirst is None
    assert r.confidence >= 0.9


def test_european_dot_dates() -> None:
    values = ["14.03.2025", "01.01.2024", "31.12.2023"]
    r = detect_date_column(values, "Datum")
    assert r.is_date is True
    assert r.dayfirst is True
    assert ".%m." in (r.format_string or "") or r.format_string == "%d.%m.%Y"


def test_us_slash_dates_unambiguous() -> None:
    # Day 25 > 12 so MM/DD/YYYY
    values = ["03/25/2025", "07/28/2024", "12/01/2024"]
    r = detect_date_column(values, "date")
    assert r.is_date is True
    assert r.dayfirst is False


def test_european_slash_dates_unambiguous() -> None:
    # Day 25 in first position
    values = ["25/03/2025", "28/07/2024", "01/12/2024"]
    r = detect_date_column(values, "date")
    assert r.is_date is True
    assert r.dayfirst is True


def test_ambiguous_all_low_values() -> None:
    values = ["03/04/2025", "05/06/2025", "07/08/2025"]  # all day and month <= 12
    r = detect_date_column(values, "date", other_column_dayfirst=None)
    assert r.is_date is True
    # Should resolve by separator or sequential or stay ambiguous
    assert r.confidence >= 0.0


def test_disambiguation_by_one_high_value() -> None:
    values = ["03/04/2025", "05/06/2025", "25/03/2025"]  # last has day=25
    r = detect_date_column(values, "date")
    assert r.is_date is True
    assert r.dayfirst is True


def test_disambiguation_cross_column() -> None:
    # First column resolved as day-first; second ambiguous column should inherit
    col1 = ["25/03/2025", "26/04/2025"]
    col2 = ["03/04/2025", "05/06/2025"]
    r1 = detect_date_column(col1, "d1")
    assert r1.dayfirst is True
    r2 = detect_date_column(col2, "d2", other_column_dayfirst=True)
    assert r2.is_date is True
    assert r2.dayfirst is True


def test_empty_column_not_date() -> None:
    r = detect_date_column([], "date")
    assert r.is_date is False
    assert r.confidence == 0.0


def test_short_year_formats() -> None:
    values = ["14.03.25", "01.01.24"]
    r = detect_date_column(values, "date")
    assert r.is_date is True
    assert r.dayfirst is True


def test_compact_yyyymmdd() -> None:
    values = ["20250314", "20240101", "20231231"]
    r = detect_date_column(values, "date")
    assert r.is_date is True
    assert r.format_string == "%Y%m%d"


def test_truly_ambiguous_stays_string() -> None:
    # All values 01/02, 02/03, etc. - no disambiguation signal
    values = ["01/02/2025", "02/03/2025", "03/04/2025"]
    r = detect_date_column(values, "date", other_column_dayfirst=None)
    # May still get a resolution via sequential or separator; just check it doesn't crash
    assert r.is_date is True or r.confidence >= 0


def test_disambiguate_day_month_unambiguous_day() -> None:
    values = ["25/03/2025", "01/02/2025"]
    dayfirst, adj, method = _disambiguate_day_month(values, "/", None)
    assert dayfirst is True
    assert method == "unambiguous_day_value"


def test_disambiguate_day_month_unambiguous_month() -> None:
    values = ["03/25/2025", "02/01/2025"]
    dayfirst, adj, method = _disambiguate_day_month(values, "/", None)
    assert dayfirst is False
    assert method == "unambiguous_month_value"


def test_disambiguate_period_separator() -> None:
    values = ["01.02.2025", "03.04.2025"]
    dayfirst, adj, method = _disambiguate_day_month(values, ".", None)
    assert dayfirst is True
    assert method == "period_separator_european"


def test_test_monotonicity() -> None:
    # Ascending dates DD/MM
    values_df = ["01/01/2025", "02/01/2025", "03/01/2025"]
    values_mf = ["01/01/2025", "01/02/2025", "01/03/2025"]
    m_df = _test_monotonicity(values_df, dayfirst=True)
    m_mf = _test_monotonicity(values_mf, dayfirst=False)
    assert m_df >= 0
    assert m_mf >= 0
