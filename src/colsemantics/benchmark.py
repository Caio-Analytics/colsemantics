import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TypedDict

from . import ContentProfile, infer_column
from .profiles import temporary_profile

_GENERIC_SEMANTIC = "Generic / Unmapped"
_EXPECTED_FIELDS = ("expected_semantic", "expected_role", "expected_domain")


class _BenchmarkEntry(TypedDict):
    profile: str
    expected: dict[str, object]
    result: dict[str, Any]


def load_cases(path: str | Path) -> list[dict[str, object]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ValueError("Benchmark cases must be a JSON list of objects.")
    return [dict(item) for item in payload]


def _profile_from_values(values: object) -> ContentProfile | None:
    if values is None:
        return None
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise ValueError("Benchmark values must be a list of strings.")
    distinct_values = sorted(set(values))
    return ContentProfile(
        data_type="Text",
        distinct_values=distinct_values,
        distinct_count=len(distinct_values),
        uniqueness_ratio=len(distinct_values) / len(values) if values else 0.0,
    )


def _required_string(case: Mapping[str, object], key: str) -> str:
    value = case.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Benchmark case requires a non-empty '{key}'.")
    return value


def _evaluate(case: Mapping[str, object]) -> _BenchmarkEntry:
    if not any(field in case for field in _EXPECTED_FIELDS):
        raise ValueError("Benchmark case requires at least one expected label.")
    profile_name = _required_string(case, "profile")
    column_name = _required_string(case, "column_name")
    detected_pattern = case.get("detected_pattern", "None")
    if not isinstance(detected_pattern, str):
        raise ValueError("Benchmark detected_pattern must be a string.")
    with temporary_profile(profile_name):
        result = infer_column(
            column_name,
            detected_pattern=detected_pattern,
            profile=_profile_from_values(case.get("values")),
        )
    return {"profile": profile_name, "expected": dict(case), "result": result}


def _accuracy(
    entries: Sequence[_BenchmarkEntry], expected_key: str, actual_key: str
) -> float | None:
    comparable = [entry for entry in entries if expected_key in entry["expected"]]
    if not comparable:
        return None
    correct = sum(
        entry["expected"][expected_key] == entry["result"][actual_key] for entry in comparable
    )
    return round(correct / len(comparable), 4)


def _metrics(entries: Sequence[_BenchmarkEntry]) -> dict[str, object]:
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for entry in entries:
        expected = entry["expected"]
        result = entry["result"]
        if "expected_semantic" in expected:
            confusion[str(expected["expected_semantic"])][str(result["semantic"])] += 1
    covered = sum(entry["result"]["semantic"] != _GENERIC_SEMANTIC for entry in entries)
    return {
        "total_cases": len(entries),
        "semantic_accuracy": _accuracy(entries, "expected_semantic", "semantic"),
        "role_accuracy": _accuracy(entries, "expected_role", "role"),
        "domain_accuracy": _accuracy(entries, "expected_domain", "domain"),
        "coverage": round(covered / len(entries), 4) if entries else 0.0,
        "confusion_matrix": {
            expected: dict(sorted(actual.items())) for expected, actual in sorted(confusion.items())
        },
    }


def evaluate_cases(cases: Sequence[Mapping[str, object]]) -> dict[str, object]:
    entries = [_evaluate(case) for case in cases]
    by_profile: dict[str, list[_BenchmarkEntry]] = defaultdict(list)
    for entry in entries:
        by_profile[str(entry["profile"])].append(entry)
    report = _metrics(entries)
    report["by_profile"] = {name: _metrics(items) for name, items in sorted(by_profile.items())}
    return report
