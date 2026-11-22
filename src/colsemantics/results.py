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
