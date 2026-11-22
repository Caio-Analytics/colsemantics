"""Accuracy floors on the benchmark sets.

Every set must reach 60% overall, and every label with at least ten cases must reach 60% on its
own, so a strong label cannot hide a weak one. The one documented exception is Checkbox columns
judged by name alone, where the name carries almost no information (see benchmarks/README.md).
"""

from pathlib import Path

import pytest

from colsemantics.benchmark import evaluate_cases, load_cases

BENCHMARKS = Path(__file__).parents[1] / "benchmarks"
MINIMUM = 0.60
MINIMUM_CASES_PER_LABEL = 10

# set name -> (overall floor, floor for every label). Floors are regression guards: raise them
# when the engine improves, never lower them to make CI pass.
FLOORS = {
    "validation": (0.92, MINIMUM),
    "holdout-v2": (0.90, MINIMUM),
    "public-br-es": (0.85, MINIMUM),
    "public-us-socrata": (0.90, MINIMUM),
    "public-us-socrata-names-only": (0.65, MINIMUM),
    "synthetic": (MINIMUM, MINIMUM),
}
# Checkbox columns judged by name alone: 40% today, kept as a regression guard only.
NAME_ONLY_FLAG_FLOOR = {"public-us-socrata-names-only": 0.35}
FLAG = "Status / Indicator / Flag"


def _report(name):
    return evaluate_cases(load_cases(BENCHMARKS / f"{name}.json"))


@pytest.mark.parametrize("name", sorted(FLOORS))
def test_overall_accuracy_floor(name):
    overall, _ = FLOORS[name]

    assert _report(name)["semantic_accuracy"] >= max(overall, MINIMUM)


@pytest.mark.parametrize("name", sorted(FLOORS))
def test_every_label_reaches_the_floor(name):
    _, per_label = FLOORS[name]
    report = _report(name)

    for label, stats in report["label_accuracy"].items():
        if stats["cases"] < MINIMUM_CASES_PER_LABEL:
            continue
        floor = NAME_ONLY_FLAG_FLOOR.get(name, per_label) if label == FLAG else per_label
        assert stats["accuracy"] >= floor, f"{name}: {label} {stats['accuracy']} < {floor}"


def test_name_only_exception_is_limited_to_checkbox_columns():
    report = _report("public-us-socrata-names-only")["label_accuracy"]

    assert report[FLAG]["accuracy"] < MINIMUM  # documented limit, not a hidden failure
    assert report["Date / Calendar"]["accuracy"] >= MINIMUM
    assert report["Geographic Location"]["accuracy"] >= MINIMUM


def test_checkbox_columns_are_flags_when_values_are_available():
    assert _report("public-us-socrata")["label_accuracy"][FLAG]["accuracy"] >= 0.95


def test_validation_corpus_is_held_out_from_calibration_fixture():
    validation = {case["column_name"] for case in load_cases(BENCHMARKS / "validation.json")}
    synthetic = {case["column_name"] for case in load_cases(BENCHMARKS / "synthetic.json")}

    assert len(validation) >= 50
    assert not validation & synthetic


def test_second_holdout_is_disjoint_from_the_first():
    first = {case["column_name"] for case in load_cases(BENCHMARKS / "validation.json")}
    second = {case["column_name"] for case in load_cases(BENCHMARKS / "holdout-v2.json")}

    assert not first & second
