import pytest
import yaml

from colsemantics import (
    export_overrides_template,
    infer_column,
    infer_csv,
    load_vocabularies,
    temporary_vocabulary,
)
from colsemantics.benchmark import load_cases


def _write(tmp_path, payload, name="vocab.yaml"):
    path = tmp_path / name
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return str(path)


def test_temporary_vocabulary_applies_only_inside_the_block(tmp_path):
    path = _write(tmp_path, {"column_overrides": {"zzq_unit": "Finance / Cost"}})

    with temporary_vocabulary(path):
        inside = infer_column("zzq_unit")
    outside = infer_column("zzq_unit")

    assert inside["domain"] == "Finance / Cost"
    assert inside["conclusive"]
    assert outside["domain"] is None


def test_temporary_vocabulary_without_paths_is_a_no_op():
    with temporary_vocabulary(None):
        assert infer_column("employee_id")["semantic"] == "Identifier (ID)"


def test_multiple_files_are_merged(tmp_path):
    first = _write(tmp_path, {"strong_categories": {"Project domain": ["workstream"]}}, "a.yaml")
    second = _write(tmp_path, {"column_overrides": {"x1": "Finance / Cost"}}, "b.yaml")

    context = load_vocabularies(f"{first}, {second}")

    assert "Project domain" in context.strong_categories
    assert context.column_overrides["x1"] == "Finance / Cost"


def test_gazetteers_from_yaml_classify_sampled_values(tmp_path):
    path = _write(
        tmp_path,
        {
            "gazetteers": [
                {
                    "name": "fruit",
                    "values": ["apple", "pear", "plum"],
                    "category": "Product / Catalog",
                    "axis": "domain",
                }
            ]
        },
    )
    source = tmp_path / "fruit.csv"
    source.write_text("f1\napple\npear\nplum\napple\n", encoding="utf-8")

    report = infer_csv(source, vocabulary_paths=path)

    assert report["columns"][0]["domain"] == "Product / Catalog"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (["not", "a", "mapping"], "YAML mapping"),
        ({"strong_categories": ["x"]}, "must map categories"),
        ({"strong_categories": {"A": "not-a-list"}}, "must be strings"),
        ({"gazetteers": "x"}, "must be a list"),
        ({"gazetteers": [{"name": "n"}]}, "Invalid gazetteer"),
        (
            {"gazetteers": [{"name": "n", "values": "x", "category": "c", "axis": "role"}]},
            "must be strings",
        ),
        (
            {"gazetteers": [{"name": "n", "values": ["x"], "category": "c", "axis": "bad"}]},
            "'role' or 'domain'",
        ),
        ({"column_overrides": ["x"]}, "map column names"),
        ({"column_overrides": {"a": 1}}, "map column names"),
    ],
)
def test_invalid_vocabularies_are_rejected(tmp_path, payload, message):
    with pytest.raises(ValueError, match=message):
        load_vocabularies(_write(tmp_path, payload))


def test_export_overrides_template_round_trips(tmp_path):
    output = tmp_path / "overrides.yaml"
    export_overrides_template(
        {"columns": [{"column": "x1", "semantic": "Finance / Cost"}]}, str(output)
    )

    assert yaml.safe_load(output.read_text(encoding="utf-8")) == {
        "column_overrides": {"x1": "Finance / Cost"}
    }


def test_benchmark_cases_must_be_a_list_of_objects(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text('{"not": "a list"}', encoding="utf-8")

    with pytest.raises(ValueError, match="JSON list"):
        load_cases(path)
