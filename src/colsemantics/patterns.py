"""Detect well-known value formats (CPF, CNPJ, e-mail, phone, postal code, UUID) in a column."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable

NO_PATTERN = "None"
MINIMUM_PATTERN_COVERAGE = 0.8

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_CEP = re.compile(r"^\d{5}-\d{3}$")
_CPF_FORMAT = re.compile(r"^(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})$")
_CNPJ_FORMAT = re.compile(r"^(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14})$")
_PHONE_BR = re.compile(r"^(\+55[\s-]?)?(\(\d{2}\)|\d{2})[\s-]?9?\d{4}-?\d{4}$")


def _digits(value: str) -> list[int]:
    return [int(char) for char in value if char.isdigit()]


def is_valid_cpf(value: str) -> bool:
    if not _CPF_FORMAT.match(value):
        return False
    digits = _digits(value)
    if len(set(digits)) == 1:
        return False
    for position in (9, 10):
        total = sum(
            digit * weight
            for digit, weight in zip(digits[:position], range(position + 1, 1, -1), strict=True)
        )
        check = (total * 10) % 11 % 10
        if digits[position] != check:
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
        total = sum(
            digit * weight for digit, weight in zip(digits[:position], weights, strict=True)
        )
        remainder = total % 11
        check = 0 if remainder < 2 else 11 - remainder
        if digits[position] != check:
            return False
    return True


def _is_formatted_phone(value: str) -> bool:
    # Bare digit strings are too ambiguous (ids, amounts): require visible phone formatting.
    return bool(_PHONE_BR.match(value)) and any(char in value for char in "()+- ")


_VALIDATORS: tuple[tuple[str, Callable[[str], bool]], ...] = (
    ("CPF", is_valid_cpf),
    ("CNPJ", is_valid_cnpj),
    ("UUID", lambda value: bool(_UUID.match(value))),
    ("E-mail", lambda value: bool(_EMAIL.match(value))),
    ("Telefone", _is_formatted_phone),
    ("CEP", lambda value: bool(_CEP.match(value))),
)


def detect_column_pattern(
    values: Iterable[str], minimum_coverage: float = MINIMUM_PATTERN_COVERAGE
) -> str:
    """Return the pattern name that at least ``minimum_coverage`` of the values match."""
    cleaned = [value.strip() for value in values if value and value.strip()]
    if not cleaned:
        return NO_PATTERN
    for name, validator in _VALIDATORS:
        matches = sum(1 for value in cleaned if validator(value))
        if matches / len(cleaned) >= minimum_coverage:
            return name
    return NO_PATTERN
