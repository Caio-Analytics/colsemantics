"""Build a ``ContentProfile`` (type, uniqueness, statistics) from raw string values."""

from __future__ import annotations

import math
import re
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .detectors import ContentProfile

_BOOLEAN_WORDS = frozenset({"true", "false", "yes", "no", "sim", "nao", "não"})
# Single letters count as Boolean only as a matched pair (y/n, t/f, s/n for sim/não).
_BOOLEAN_LETTER_PAIRS = (frozenset("yn"), frozenset("tf"), frozenset("sn"))
_PLAIN_NUMBER = re.compile(r"^-?\d+([.,]\d+)?$")
_BR_NUMBER = re.compile(r"^-?\d{1,3}(\.\d{3})+,\d+$")
_US_NUMBER = re.compile(r"^-?\d{1,3}(,\d{3})+\.\d+$")
_ISO_DATE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$"
)
_SLASH_DATE = re.compile(
    r"^(\d{1,2})/(\d{1,2})/(\d{4})(\s+\d{1,2}:\d{2}(:\d{2})?(\s*[AaPp][Mm])?)?$"
)


def parse_number(value: str) -> float | None:
    """Parse plain, Brazilian (1.234,56), and US (1,234.56) numbers; return None otherwise."""
    text = value.strip()
    if _BR_NUMBER.match(text):
        text = text.replace(".", "").replace(",", ".")
    elif _US_NUMBER.match(text):
        text = text.replace(",", "")
    elif _PLAIN_NUMBER.match(text):
        text = text.replace(",", ".")
    else:
        return None
    return float(text)


def _has_leading_zero(value: str) -> bool:
    digits = value.lstrip("-")
    return len(digits) > 1 and digits.startswith("0") and digits[1].isdigit()


def _is_date(value: str) -> bool:
    text = value.strip()
    iso = _ISO_DATE.match(text)
    candidates: list[tuple[int, int, int]] = []
    if iso:
        candidates.append((int(iso[1]), int(iso[2]), int(iso[3])))
    slash = _SLASH_DATE.match(text)
    if slash:
        first, second, year = int(slash[1]), int(slash[2]), int(slash[3])
        candidates += [(year, second, first), (year, first, second)]  # dd/mm or mm/dd
    for year, month, day in candidates:
        try:
            date(year, month, day)
        except ValueError:
            continue
        return True
    return False


def detect_data_type(values: list[str]) -> str:
    """Return Boolean, Integer, Decimal, Date, or Text for non-empty values."""
    if not values:
        return "Text"
    lowered = {value.strip().lower() for value in values}
    if lowered <= _BOOLEAN_WORDS or any(lowered <= pair for pair in _BOOLEAN_LETTER_PAIRS):
        return "Boolean"
    if all(_is_date(value) for value in values):
        return "Date"
    numbers = [parse_number(value) for value in values]
    if all(number is not None for number in numbers) and not any(
        _has_leading_zero(value.strip()) for value in values
    ):
        if all(re.fullmatch(r"-?\d+", value.strip()) for value in values):
            return "Integer"
        return "Decimal"
    return "Text"


def _skewness(numbers: list[float]) -> float | None:
    count = len(numbers)
    if count < 3:
        return None
    mean = sum(numbers) / count
    variance = sum((number - mean) ** 2 for number in numbers) / count
    if variance == 0:
        return None
    return (sum((number - mean) ** 3 for number in numbers) / count) / math.pow(variance, 1.5)


def _decimal_places(value: str) -> int:
    text = value.strip()
    match = re.search(r"[.,](\d+)$", text)
    return len(match[1]) if match else 0


def profile_values(values: list[str]) -> ContentProfile:
    """Profile non-empty string values in their original order."""
    from .detectors import ContentProfile

    distinct_values = sorted(set(values))
    total = len(values)
    data_type = detect_data_type(values)
    profile = ContentProfile(
        data_type=data_type,
        distinct_values=distinct_values,
        distinct_count=len(distinct_values),
        uniqueness_ratio=len(distinct_values) / total if total else 0.0,
        mean_string_length=sum(len(value) for value in values) / total if total else None,
        fixed_length=len({len(value) for value in values}) == 1 if total else False,
    )
    if data_type in ("Integer", "Decimal"):
        numbers = [number for value in values if (number := parse_number(value)) is not None]
        profile.minimum = min(numbers)
        profile.skewness = _skewness(numbers)
        profile.monotonically_increasing = all(
            later > earlier for earlier, later in zip(numbers, numbers[1:], strict=False)
        )
        if data_type == "Decimal":
            places = {_decimal_places(value) for value in values}
            profile.fixed_decimal_places = places.pop() if len(places) == 1 else None
    return profile
