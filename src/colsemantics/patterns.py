"""Detect well-known value formats (and their locale) in a column of string values.

Supported types: ``cpf``, ``cnpj``, ``ssn``, ``ein``, ``uuid``, ``email``, ``phone``,
``postal_code``, and ``address``. Brazilian (BR) and US formats are recognized; detection looks
at values only, so it does not depend on the vocabulary profile.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .results import PatternInfo

NO_PATTERN = "None"
MINIMUM_PATTERN_COVERAGE = 0.8

_LEGACY_NAMES = {
    "cpf": "cpf",
    "cnpj": "cnpj",
    "ssn": "ssn",
    "ein": "ein",
    "uuid": "uuid",
    "e-mail": "email",
    "email": "email",
    "telefone": "phone",
    "phone": "phone",
    "cep": "postal_code",
    "zip": "postal_code",
    "postal_code": "postal_code",
    "address": "address",
}
PATTERN_LABELS = {
    "cpf": "CPF",
    "cnpj": "CNPJ",
    "ssn": "SSN",
    "ein": "EIN",
    "uuid": "UUID",
    "email": "e-mail",
    "phone": "phone number",
    "postal_code": "postal code",
    "address": "street address",
}
LOCALE_NAMES = {"BR": "Brazilian", "US": "US"}


def canonical_pattern(name: str) -> str:
    """Map pattern names (including legacy ``E-mail``, ``Telefone``, ``CEP``) to English keys."""
    key = name.strip().lower()
    return _LEGACY_NAMES.get(key, NO_PATTERN if name == NO_PATTERN else name)


@dataclass(frozen=True)
class ValueMatch:
    locale: str | None
    variant: str | None
    format: str | None
    validated: bool


# --- Brazilian and US identifiers -----------------------------------------------------------

_CPF_FORMAT = re.compile(r"^(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})$")
_CNPJ_FORMAT = re.compile(r"^(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14})$")
_SSN = re.compile(r"^(\d{3})-(\d{2})-(\d{4})$")
_EIN = re.compile(r"^(\d{2})-(\d{7})$")


def _digits(value: str) -> list[int]:
    return [int(char) for char in value if char.isdigit()]


def is_valid_cpf(value: str) -> bool:
    if not _CPF_FORMAT.match(value):
        return False
    digits = _digits(value)
    if len(set(digits)) == 1:
        return False
    for position in (9, 10):
        weights = range(position + 1, 1, -1)
        total = sum(d * w for d, w in zip(digits[:position], weights, strict=True))
        if digits[position] != (total * 10) % 11 % 10:
            return False
    return True


def is_valid_cnpj(value: str) -> bool:
    if not _CNPJ_FORMAT.match(value):
        return False
    digits = _digits(value)
    if len(set(digits)) == 1:
        return False
    for position, weights in (
        (12, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]),
        (13, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]),
    ):
        total = sum(d * w for d, w in zip(digits[:position], weights, strict=True))
        remainder = total % 11
        if digits[position] != (0 if remainder < 2 else 11 - remainder):
            return False
    return True


def is_valid_ssn(value: str) -> bool:
    """Format ``AAA-GG-SSSS`` with the area, group, and serial ranges the SSA issues."""
    match = _SSN.match(value)
    if not match:
        return False
    area, group, serial = match.groups()
    return (
        area not in ("000", "666")
        and not area.startswith("9")
        and group != "00"
        and (serial != "0000")
    )


def _cpf(value: str) -> ValueMatch | None:
    if not is_valid_cpf(value):
        return None
    return ValueMatch("BR", "formatted" if "." in value else "digits", "NNN.NNN.NNN-NN", True)


def _cnpj(value: str) -> ValueMatch | None:
    if not is_valid_cnpj(value):
        return None
    return ValueMatch("BR", None, "NN.NNN.NNN/NNNN-NN", True)


def _ssn(value: str) -> ValueMatch | None:
    return ValueMatch("US", None, "NNN-NN-NNNN", True) if is_valid_ssn(value) else None


def _ein(value: str) -> ValueMatch | None:
    return ValueMatch("US", None, "NN-NNNNNNN", False) if _EIN.match(value) else None


# --- Generic formats ------------------------------------------------------------------------

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _email(value: str) -> ValueMatch | None:
    return ValueMatch(None, None, "name@domain.tld", True) if _EMAIL.match(value) else None


def _uuid(value: str) -> ValueMatch | None:
    return ValueMatch(None, None, "8-4-4-4-12 hex", True) if _UUID.match(value) else None


# --- Phones ---------------------------------------------------------------------------------

# Valid Brazilian area codes (DDD).
_BR_AREA_CODES = frozenset(
    {
        *range(11, 20),
        21, 22, 24, 27, 28,
        *range(31, 36), 37, 38,
        *range(41, 50),
        51, 53, 54, 55,
        *range(61, 70),
        71, 73, 74, 75, 77, 79,
        *range(81, 90),
        *range(91, 100),
    }
)  # fmt: skip

_BR_PHONE_FORMATTED = re.compile(
    r"^(?P<cc>\+55[\s-]?)?(?:\((?P<a1>\d{2})\)|(?P<a2>\d{2}))[\s-]?(?P<lead>9?)(?P<p1>\d{4})[\s-]?(?P<p2>\d{4})$"
)
_BR_PHONE_INTL_DIGITS = re.compile(r"^\+55(\d{2})(9?\d{8})$")
_BR_TOLL_FREE = re.compile(r"^0[38]00[\s-]?\d{3}[\s-]?\d{4}$")

_US_PHONE_FORMATTED = re.compile(
    r"^(?P<cc>\+?1[\s.-]?)?(?:\((?P<a1>\d{3})\)|(?P<a2>\d{3}))[\s.-]?(?P<ex>\d{3})[\s.-]?(?P<ln>\d{4})$"
)
_US_PHONE_INTL_DIGITS = re.compile(r"^\+1(\d{3})(\d{3})(\d{4})$")


def _br_phone(value: str) -> ValueMatch | None:
    if _BR_TOLL_FREE.match(value):
        return ValueMatch("BR", "toll-free", "0800 NNN NNNN", True)
    intl = _BR_PHONE_INTL_DIGITS.match(value)
    if intl:
        area, number = intl.groups()
        variant = "mobile" if len(number) == 9 and number[0] == "9" else "landline"
        ok = int(area) in _BR_AREA_CODES and (variant == "mobile" or number[0] in "2345")
        return ValueMatch("BR", variant, "+55DDNNNNNNNNN", ok) if ok else None
    match = _BR_PHONE_FORMATTED.match(value)
    if not match or not any(char in value for char in "()+- "):
        return None
    area = int(match["a1"] or match["a2"])
    mobile = bool(match["lead"])
    if area not in _BR_AREA_CODES or (not mobile and match["p1"][0] not in "2345"):
        return None
    international = bool(match["cc"])
    parenthesized = match["a1"] is not None
    mask = ("(DD) " if parenthesized else "DD ") + ("9NNNN-NNNN" if mobile else "NNNN-NNNN")
    return ValueMatch(
        "BR",
        "mobile" if mobile else "landline",
        ("+55 " + mask) if international else mask,
        True,
    )


def _us_phone(value: str) -> ValueMatch | None:
    intl = _US_PHONE_INTL_DIGITS.match(value)
    if intl:
        area, exchange, line = intl.groups()
        ok = _valid_nanp(area, exchange)
        return ValueMatch("US", None, "+1NNNNNNNNNN", True) if ok else None
    match = _US_PHONE_FORMATTED.match(value)
    if not match or not any(char in value for char in "()+-. "):
        return None
    area = match["a1"] or match["a2"]
    if not _valid_nanp(area, match["ex"]):
        return None
    if match["a1"]:
        mask = "(NNN) NNN-NNNN"
    elif "." in value:
        mask = "NNN.NNN.NNNN"
    else:
        mask = "NNN-NNN-NNNN"
    return ValueMatch("US", None, ("+1 " + mask) if match["cc"] else mask, True)


def _valid_nanp(area: str, exchange: str) -> bool:
    """NANP: area code and exchange start with 2-9 and are not N11 service codes."""
    return all(part[0] in "23456789" and part[1:] != "11" for part in (area, exchange))


def _phone(value: str) -> ValueMatch | None:
    # Bare digit strings are too ambiguous (ids, amounts): require formatting or a + prefix.
    # Brazilian is tried first only when the area code is a valid DDD in a two-digit group;
    # the groupings differ, so the two formats do not overlap in practice.
    return _br_phone(value) or _us_phone(value)


# --- Postal codes ---------------------------------------------------------------------------

_CEP = re.compile(r"^\d{5}-\d{3}$")
_ZIP_PLUS4 = re.compile(r"^\d{5}-\d{4}$")


def _postal_code(value: str) -> ValueMatch | None:
    if _CEP.match(value):
        return ValueMatch("BR", "CEP", "NNNNN-NNN", True)
    if _ZIP_PLUS4.match(value):
        return ValueMatch("US", "ZIP+4", "NNNNN-NNNN", True)
    return None


# --- Street addresses -----------------------------------------------------------------------


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).lower().strip()


_BR_STREET_TYPES = (
    r"rua|r\.|avenida|av\.?|alameda|al\.|travessa|tv\.|praca|pca\.?|estrada|est\.|rodovia|rod\.|"
    r"largo|viela|via|beco|ladeira|caminho"
)
_BR_ADDRESS = re.compile(
    rf"^(?:{_BR_STREET_TYPES})\s+[^\d,]+?(?:[,\s]\s*(?:n[ºo°.]?\s*)?(?:\d+[a-z]?|s/n)\b|\s+km\s*\d+)"
)
_BR_HIGHWAY = re.compile(r"^(?:rodovia|rod\.|estrada|est\.)\s+.+\bkm\s*\d+")
_US_STREET_SUFFIXES = (
    r"st|street|ave|avenue|blvd|boulevard|rd|road|dr|drive|ln|lane|ct|court|way|pl|place|"
    r"pkwy|parkway|hwy|highway|cir|circle|ter|terrace|sq|square|trl|trail"
)
_US_ADDRESS = re.compile(
    rf"^\d+[a-z]?\s+(?:(?:n|s|e|w|north|south|east|west)\.?\s+)?[a-z0-9.'\- ]+?\s+(?:{_US_STREET_SUFFIXES})\b\.?"
    r"(?:\s+(?:n|s|e|w|ne|nw|se|sw)\b\.?)?(?:[,\s].*)?$"
)
_US_PO_BOX = re.compile(r"^p\.?\s?o\.?\s+box\s+\d+")


def _address(value: str) -> ValueMatch | None:
    text = _fold(value)
    if len(text) < 6 or len(text) > 120:
        return None
    if _US_PO_BOX.match(text):
        return ValueMatch("US", "po_box", "PO Box NNN", False)
    if _BR_ADDRESS.match(text) or _BR_HIGHWAY.match(text):
        full = bool(re.search(r"\b\d{5}-?\d{3}\b|\b[a-z]{2}\b$", text)) and "," in text
        return ValueMatch("BR", "full" if full else "street", "Rua Nome, NNN", False)
    if _US_ADDRESS.match(text):
        full = bool(re.search(r"\b[a-z]{2}\s+\d{5}(-\d{4})?\b", text))
        return ValueMatch("US", "full" if full else "street", "NNN Name St", False)
    return None


# --- Registry and column-level analysis -------------------------------------------------------

# (type, matcher, minimum coverage). Order matters: more specific formats first.
_DETECTORS: tuple[tuple[str, Callable[[str], ValueMatch | None], float], ...] = (
    ("cpf", _cpf, MINIMUM_PATTERN_COVERAGE),
    ("cnpj", _cnpj, MINIMUM_PATTERN_COVERAGE),
    ("ssn", _ssn, MINIMUM_PATTERN_COVERAGE),
    ("ein", _ein, MINIMUM_PATTERN_COVERAGE),
    ("uuid", _uuid, MINIMUM_PATTERN_COVERAGE),
    ("email", _email, MINIMUM_PATTERN_COVERAGE),
    ("phone", _phone, MINIMUM_PATTERN_COVERAGE),
    ("postal_code", _postal_code, MINIMUM_PATTERN_COVERAGE),
    ("address", _address, 0.6),  # free-form, so a looser bar
)


def describe_pattern(info: PatternInfo) -> str:
    """Human-readable description, for example ``Brazilian mobile phone number``."""
    parts = [
        LOCALE_NAMES.get(info["locale"] or "", ""),
        info["variant"] or "" if info["type"] in ("phone", "address") else "",
        PATTERN_LABELS.get(info["type"], info["type"]),
    ]
    return " ".join(part for part in parts if part)


def _build_info(
    pattern_type: str, matches: list[ValueMatch], total: int, minimum_coverage: float
) -> PatternInfo | None:
    coverage = len(matches) / total
    if coverage < minimum_coverage:
        return None
    locales = Counter(match.locale for match in matches if match.locale)
    variants = Counter(match.variant for match in matches if match.variant)
    formats = Counter(match.format for match in matches if match.format)
    info: PatternInfo = {
        "type": pattern_type,
        "locale": locales.most_common(1)[0][0] if locales else None,
        "variant": variants.most_common(1)[0][0] if variants else None,
        "format": formats.most_common(1)[0][0] if formats else None,
        "coverage": round(coverage, 4),
        "validated": all(match.validated for match in matches),
        "message": "",
    }
    shown = f" (e.g. {info['format']})" if info["format"] else ""
    info["message"] = (
        f"{coverage:.0%} of sampled values look like a {describe_pattern(info)}{shown}"
    )
    return info


def analyze_values(
    values: Iterable[str],
    minimum_coverage: float | None = None,
    expected_type: str | None = None,
) -> PatternInfo | None:
    """Describe the dominant value format of a column, or ``None`` when there is none.

    ``expected_type`` restricts the search to one pattern type. ``minimum_coverage`` overrides
    each detector's default bar.
    """
    cleaned = [value.strip() for value in values if value and value.strip()]
    if not cleaned:
        return None
    for pattern_type, matcher, default_coverage in _DETECTORS:
        if expected_type is not None and pattern_type != expected_type:
            continue
        matches = [match for value in cleaned if (match := matcher(value)) is not None]
        if not matches:
            continue
        info = _build_info(
            pattern_type,
            matches,
            len(cleaned),
            default_coverage if minimum_coverage is None else minimum_coverage,
        )
        if info is not None:
            return info
    return None


def detect_column_pattern(
    values: Iterable[str], minimum_coverage: float = MINIMUM_PATTERN_COVERAGE
) -> str:
    """Return the pattern type that at least ``minimum_coverage`` of the values match."""
    info = analyze_values(values, minimum_coverage)
    return info["type"] if info else NO_PATTERN
