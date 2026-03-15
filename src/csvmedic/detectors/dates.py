"""
Statistical date format detection and DD-MM vs MM-DD disambiguation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

# Regex patterns ordered from most specific to least specific
# (regex, strptime_format, dayfirst) — dayfirst None = ambiguous
DATE_PATTERNS: list[tuple[str, str | None, bool | None]] = [
    (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "%Y-%m-%dT%H:%M:%S", None),
    (r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "%Y-%m-%d %H:%M:%S", None),
    (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d", None),
    (r"\d{2}\.\d{2}\.\d{4}", "%d.%m.%Y", True),
    (r"\d{1,2}\.\d{1,2}\.\d{4}", "%d.%m.%Y", True),
    (r"\d{2}\.\d{2}\.\d{2}", "%d.%m.%y", True),
    (r"\d{2}/\d{2}/\d{4}", None, None),
    (r"\d{1,2}/\d{1,2}/\d{4}", None, None),
    (r"\d{2}/\d{2}/\d{2}", None, None),
    (r"\d{2}-\d{2}-\d{4}", None, None),
    (r"\d{1,2}-\d{1,2}-\d{4}", None, None),
    (r"\d{8}", None, None),
]

MONTH_NAMES: dict[str, dict[str, int]] = {
    "en": {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    },
    "de": {
        "januar": 1,
        "februar": 2,
        "märz": 3,
        "april": 4,
        "mai": 5,
        "juni": 6,
        "juli": 7,
        "august": 8,
        "september": 9,
        "oktober": 10,
        "november": 11,
        "dezember": 12,
        "jan": 1,
        "feb": 2,
        "mär": 3,
        "apr": 4,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "okt": 10,
        "nov": 11,
        "dez": 12,
    },
    "fr": {
        "janvier": 1,
        "février": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "août": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "décembre": 12,
        "janv": 1,
        "févr": 2,
        "avr": 4,
        "juil": 7,
        "sept": 9,
        "oct": 10,
        "nov": 11,
        "déc": 12,
    },
    "es": {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    },
    "nl": {
        "januari": 1,
        "februari": 2,
        "maart": 3,
        "april": 4,
        "mei": 5,
        "juni": 6,
        "juli": 7,
        "augustus": 8,
        "september": 9,
        "oktober": 10,
        "november": 11,
        "december": 12,
    },
    "pt": {
        "janeiro": 1,
        "fevereiro": 2,
        "março": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12,
    },
    "it": {
        "gennaio": 1,
        "febbraio": 2,
        "marzo": 3,
        "aprile": 4,
        "maggio": 5,
        "giugno": 6,
        "luglio": 7,
        "agosto": 8,
        "settembre": 9,
        "ottobre": 10,
        "novembre": 11,
        "dicembre": 12,
    },
}


@dataclass
class DateDetectionResult:
    """Result of date detection for a single column."""

    is_date: bool
    format_string: str | None
    dayfirst: bool | None
    confidence: float
    ambiguous_count: int
    unambiguous_count: int
    parse_success_rate: float
    disambiguation_method: str | None
    sample_values: list[str]


def _match_date_patterns(values: list[str]) -> tuple[str | None, str | None, bool | None, str]:
    """Find best-matching date pattern. Returns (regex_used, strptime_fmt, dayfirst, separator)."""
    filtered = [v.strip() for v in values if v and v.strip()]
    if not filtered:
        return (None, None, None, "")

    # Count matches per pattern
    best_match_count = 0
    best_regex: str | None = None
    best_fmt: str | None = None
    best_dayfirst: bool | None = None
    best_sep = ""

    for regex, fmt, dayfirst in DATE_PATTERNS:
        pat = re.compile(regex)
        count = sum(1 for v in filtered if pat.fullmatch(v.strip()))
        if count > best_match_count and count >= len(filtered) * 0.5:
            best_match_count = count
            best_regex = regex
            best_fmt = fmt
            best_dayfirst = dayfirst
            if filtered:
                s = filtered[0]
                if "/" in s:
                    best_sep = "/"
                elif "-" in s and not re.match(r"\d{4}-\d{2}-\d{2}", s):
                    best_sep = "-"
                elif "." in s:
                    best_sep = "."

    if best_fmt:
        return (best_regex, best_fmt, best_dayfirst, best_sep)

    # Ambiguous slash/dash: need strptime format from disambiguation
    if best_regex and best_match_count >= len(filtered) * 0.5:
        return (best_regex, None, None, best_sep)

    return (None, None, None, "")


def _parse_with_format(value: str, fmt: str, dayfirst: bool | None) -> datetime | None:
    """Parse one value with given strptime format (already resolved)."""
    value = value.strip()
    try:
        return datetime.strptime(value, fmt)
    except ValueError:
        return None


def _ambiguous_slash_format(dayfirst: bool) -> str:
    """Return strptime format for DD/MM/YYYY or MM/DD/YYYY."""
    return "%d/%m/%Y" if dayfirst else "%m/%d/%Y"


def _ambiguous_dash_format(dayfirst: bool) -> str:
    return "%d-%m-%Y" if dayfirst else "%m-%d-%Y"


def _test_monotonicity(values: list[str], dayfirst: bool) -> float:
    """Test how monotonic the dates are under the given interpretation. Return ratio in [0,1]."""
    sep = "/" if "/" in (values[0] if values else "") else "-"
    fmt = _ambiguous_slash_format(dayfirst) if sep == "/" else _ambiguous_dash_format(dayfirst)
    parsed: list[datetime] = []
    for v in values:
        p = _parse_with_format(v.strip(), fmt, dayfirst)
        if p is not None:
            parsed.append(p)
    if len(parsed) < 2:
        return 0.0
    monotonic = 0
    for i in range(1, len(parsed)):
        if parsed[i] >= parsed[i - 1]:
            monotonic += 1
    return monotonic / (len(parsed) - 1)


def _disambiguate_day_month(
    values: list[str],
    separator: str,
    other_column_dayfirst: bool | None,
) -> tuple[bool | None, float, str | None]:
    """Disambiguate DD/MM vs MM/DD. Returns (dayfirst, confidence_adjustment, method)."""
    first_components: list[int] = []
    second_components: list[int] = []
    for v in values:
        v = v.strip()
        parts = re.split(r"[/\-.]", v)
        if len(parts) >= 2 and re.match(r"^\d{4}$", parts[-1].strip()):
            try:
                first_components.append(int(parts[0]))
                second_components.append(int(parts[1]))
            except ValueError:
                continue

    if any(f > 12 for f in first_components):
        return (True, 0.15, "unambiguous_day_value")
    if any(s > 12 for s in second_components):
        return (False, 0.15, "unambiguous_month_value")

    if other_column_dayfirst is not None:
        return (other_column_dayfirst, 0.10, "cross_column_inference")

    if separator == ".":
        return (True, 0.08, "period_separator_european")

    monotonic_df = _test_monotonicity(values, dayfirst=True)
    monotonic_mf = _test_monotonicity(values, dayfirst=False)
    if monotonic_df > monotonic_mf:
        return (True, 0.05, "sequential_analysis")
    if monotonic_mf > monotonic_df:
        return (False, 0.05, "sequential_analysis")

    return (None, -0.20, None)


def _parse_named_month(value: str) -> datetime | None:
    """Try to parse named month formats like '01 Jan 2025' or '1. März 2025'."""
    value = value.strip()
    # Try pattern: day month_name year
    for lang, names in MONTH_NAMES.items():
        for month_name, num in names.items():
            if month_name in value.lower():
                # Replace month name with number and try strptime
                pat = re.compile(re.escape(month_name), re.I)
                for fmt in ("%d %m %Y", "%d.%m.%Y", "%d %b %Y", "%B %d, %Y"):
                    try:
                        test = pat.sub(str(num).zfill(2), value.lower())
                        # Normalize to "dd mm yyyy"
                        parts = re.split(r"[\s.,]+", test)
                        if len(parts) >= 3:
                            day, mon, year = parts[0], parts[1], parts[2]
                            if len(year) == 2:
                                year = "20" + year
                            return datetime(int(year), int(mon), int(day))
                    except (ValueError, IndexError):
                        continue
    return None


def _try_compact_yyyymmdd(value: str) -> datetime | None:
    """Parse 8-digit YYYYMMDD."""
    value = value.strip()
    if re.fullmatch(r"\d{8}", value):
        try:
            return datetime(int(value[:4]), int(value[4:6]), int(value[6:8]))
        except ValueError:
            pass
    return None


def detect_date_column(
    values: list[str],
    column_name: str,
    other_column_dayfirst: bool | None = None,
) -> DateDetectionResult:
    """Analyze string values and determine if they represent dates."""
    filtered = [v.strip() for v in values if v and v.strip()]
    if not filtered:
        return DateDetectionResult(
            is_date=False,
            format_string=None,
            dayfirst=None,
            confidence=0.0,
            ambiguous_count=0,
            unambiguous_count=0,
            parse_success_rate=0.0,
            disambiguation_method=None,
            sample_values=[],
        )

    regex_used, fmt, dayfirst_hint, separator = _match_date_patterns(filtered)
    if regex_used is None:
        # Try named month
        parsed = sum(1 for v in filtered if _parse_named_month(v) is not None)
        if parsed >= len(filtered) * 0.5:
            return DateDetectionResult(
                is_date=True,
                format_string="named_month",
                dayfirst=True,
                confidence=0.9,
                ambiguous_count=0,
                unambiguous_count=parsed,
                parse_success_rate=parsed / len(filtered),
                disambiguation_method="named_month",
                sample_values=filtered[:5],
            )
        # Try compact YYYYMMDD
        parsed_compact = sum(1 for v in filtered if _try_compact_yyyymmdd(v) is not None)
        if parsed_compact >= len(filtered) * 0.5:
            return DateDetectionResult(
                is_date=True,
                format_string="%Y%m%d",
                dayfirst=None,
                confidence=0.95,
                ambiguous_count=0,
                unambiguous_count=parsed_compact,
                parse_success_rate=parsed_compact / len(filtered),
                disambiguation_method="compact_yyyymmdd",
                sample_values=filtered[:5],
            )
        return DateDetectionResult(
            is_date=False,
            format_string=None,
            dayfirst=None,
            confidence=0.0,
            ambiguous_count=0,
            unambiguous_count=0,
            parse_success_rate=0.0,
            disambiguation_method=None,
            sample_values=filtered[:5],
        )

    # Compact 8-digit (YYYYMMDD): try that first before generic disambiguation
    if regex_used == r"\d{8}" and separator == "":
        parsed_compact = sum(1 for v in filtered if _try_compact_yyyymmdd(v) is not None)
        if parsed_compact >= len(filtered) * 0.5:
            return DateDetectionResult(
                is_date=True,
                format_string="%Y%m%d",
                dayfirst=None,
                confidence=0.95,
                ambiguous_count=0,
                unambiguous_count=parsed_compact,
                parse_success_rate=parsed_compact / len(filtered),
                disambiguation_method="compact_yyyymmdd",
                sample_values=filtered[:5],
            )

    # Build format if ambiguous (slash or dash, no ISO)
    disambiguation_method: str | None = None
    confidence_adj = 0.0
    if fmt is None:
        dayfirst, adj, method = _disambiguate_day_month(filtered, separator, other_column_dayfirst)
        if dayfirst is None:
            return DateDetectionResult(
                is_date=True,
                format_string=None,
                dayfirst=None,
                confidence=max(0.0, 0.5 + adj),
                ambiguous_count=len(filtered),
                unambiguous_count=0,
                parse_success_rate=1.0,
                disambiguation_method=None,
                sample_values=filtered[:5],
            )
        fmt = (
            _ambiguous_slash_format(dayfirst)
            if separator == "/"
            else _ambiguous_dash_format(dayfirst)
        )
        dayfirst_hint = dayfirst
        disambiguation_method = method
        confidence_adj = adj
    else:
        dayfirst = dayfirst_hint

    # Parse with format and collect components for ambiguous count
    parse_ok = 0
    parse_fail = 0
    first_components: list[int] = []
    second_components: list[int] = []
    for v in filtered:
        if fmt == "%Y%m%d":
            if _try_compact_yyyymmdd(v) is not None:
                parse_ok += 1
            else:
                parse_fail += 1
        else:
            p = _parse_with_format(v, fmt, dayfirst)
            if p is not None:
                parse_ok += 1
            else:
                parse_fail += 1
            if separator and separator in v:
                parts = re.split(r"[/\-.]", v.strip())
                if len(parts) >= 2 and re.search(r"\d{4}", v):
                    try:
                        first_components.append(int(parts[0]))
                        second_components.append(int(parts[1]))
                    except ValueError:
                        pass

    total = len(filtered)
    parse_success_rate = parse_ok / total if total else 0.0
    ambiguous_count = sum(
        1 for a, b in zip(first_components, second_components) if a <= 12 and b <= 12
    )
    unambiguous_count = sum(
        1 for a, b in zip(first_components, second_components) if a > 12 or b > 12
    )

    confidence = 1.0 - 0.05 * parse_fail + confidence_adj
    confidence = max(0.0, min(1.0, confidence))

    return DateDetectionResult(
        is_date=parse_success_rate >= 0.5,
        format_string=fmt,
        dayfirst=dayfirst,
        confidence=confidence,
        ambiguous_count=ambiguous_count,
        unambiguous_count=unambiguous_count,
        parse_success_rate=parse_success_rate,
        disambiguation_method=disambiguation_method,
        sample_values=filtered[:5],
    )
