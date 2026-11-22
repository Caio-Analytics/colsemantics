"""Typed shapes of the dictionaries returned by the public inference functions."""

from __future__ import annotations

from typing import TypedDict


class Sensitivity(TypedDict):
    level: str
    action: str
    reason: str


class Hypothesis(TypedDict):
    semantic: str
    axis: str
    confidence: float
    evidence: list[str]


class PatternInfo(TypedDict):
    """A value format found in the column, for example a Brazilian mobile phone number."""

    type: str  # cpf, cnpj, ssn, ein, uuid, email, phone, postal_code, address
    locale: str | None  # "BR" or "US" when the format is country-specific
    variant: str | None  # for example "mobile", "landline", "CEP", "ZIP+4", "street"
    format: str | None  # most common mask, for example "(DD) 9NNNN-NNNN"
    coverage: float | None  # share of sampled values that match; None if reported by the caller
    validated: bool  # True when a checksum or numbering-plan rule confirmed the values
    message: str


class InferenceResult(TypedDict):
    semantic: str
    role: str | None
    domain: str | None
    raw_confidence: float
    confidence: float
    evidence: str
    conclusive: bool
    review_required: bool
    sensitivity: Sensitivity
    pattern: PatternInfo | None
    hypotheses: list[Hypothesis]


class CsvColumnResult(InferenceResult):
    column_name: str
    column_index: int


class CsvSource(TypedDict):
    path: str
    format: str
    encoding: str
    delimiter: str


class CsvReport(TypedDict):
    source: CsvSource
    profile: str
    sampling: str
    sample_size: int
    rows_read: int
    rows_sampled: int
    rows_malformed: int
    warnings: list[str]
    columns: list[CsvColumnResult]
    summary: dict[str, int]
