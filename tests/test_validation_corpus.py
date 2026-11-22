from pathlib import Path

from colsemantics.benchmark import evaluate_cases, load_cases

BENCHMARKS = Path(__file__).parents[1] / "benchmarks"
VALIDATION = BENCHMARKS / "validation.json"
HOLDOUT_V2 = BENCHMARKS / "holdout-v2.json"

# Regression floors. Raise them when the engine improves; never lower them to make CI pass.
MINIMUM_SEMANTIC_ACCURACY = 0.92
MINIMUM_HOLDOUT_V2_ACCURACY = 0.90
MINIMUM_PUBLIC_BR_ACCURACY = 0.85
MINIMUM_PUBLIC_US_ACCURACY = 0.60


def test_validation_corpus_is_held_out_from_calibration_fixture():
    validation = {case["column_name"] for case in load_cases(VALIDATION)}
    synthetic = {
        case["column_name"]
        for case in load_cases(Path(__file__).parents[1] / "benchmarks" / "synthetic.json")
    }
    assert len(validation) >= 50
    assert not validation & synthetic


def test_validation_accuracy_does_not_regress():
    report = evaluate_cases(load_cases(VALIDATION))

    assert report["semantic_accuracy"] >= MINIMUM_SEMANTIC_ACCURACY


def test_second_holdout_does_not_regress_and_is_disjoint():
    first = {case["column_name"] for case in load_cases(VALIDATION)}
    second = load_cases(HOLDOUT_V2)

    assert not first & {case["column_name"] for case in second}
    assert evaluate_cases(second)["semantic_accuracy"] >= MINIMUM_HOLDOUT_V2_ACCURACY


def test_public_catalog_samples_do_not_regress():
    br = evaluate_cases(load_cases(BENCHMARKS / "public-br-es.json"))
    us = evaluate_cases(load_cases(BENCHMARKS / "public-us-socrata.json"))

    assert br["semantic_accuracy"] >= MINIMUM_PUBLIC_BR_ACCURACY
    assert us["semantic_accuracy"] >= MINIMUM_PUBLIC_US_ACCURACY
