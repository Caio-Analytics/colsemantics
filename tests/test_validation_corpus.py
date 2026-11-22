from pathlib import Path

from colsemantics.benchmark import evaluate_cases, load_cases

VALIDATION = Path(__file__).parents[1] / "benchmarks" / "validation.json"

# Regression floors. Raise them when the engine improves; never lower them to make CI pass.
MINIMUM_SEMANTIC_ACCURACY = 0.70


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
