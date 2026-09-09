import pytest

from colsemantics.benchmark import evaluate_cases, load_cases


def test_reports_accuracy_coverage_and_confusion_matrix():
    report = evaluate_cases(
        [
            {
                "profile": "pt-BR",
                "column_name": "employee_id",
                "expected_semantic": "Identifier (ID)",
            },
            {
                "profile": "pt-BR",
                "column_name": "unknown",
                "expected_semantic": "Generic / Unmapped",
            },
        ]
    )

    assert report["semantic_accuracy"] == 1.0
    assert report["coverage"] == 0.5
    assert report["confusion_matrix"] == {
        "Generic / Unmapped": {"Generic / Unmapped": 1},
        "Identifier (ID)": {"Identifier (ID)": 1},
    }


def test_reports_metrics_by_profile():
    report = evaluate_cases(
        [
            {
                "profile": "pt-BR",
                "column_name": "employee_id",
                "expected_semantic": "Identifier (ID)",
            }
        ]
    )

    assert report["by_profile"]["pt-BR"]["total_cases"] == 1


def test_rejects_cases_without_an_expected_label():
    with pytest.raises(ValueError, match="expected"):
        evaluate_cases([{"profile": "pt-BR", "column_name": "employee_id"}])


def test_rejects_a_non_list_benchmark_fixture(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text('{"column_name": "employee_id"}', encoding="utf-8")

    with pytest.raises(ValueError, match="JSON list"):
        load_cases(path)
