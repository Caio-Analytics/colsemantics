import pytest

from colsemantics.csv_inference import infer_csv


def test_infers_csv_columns_from_a_bounded_sample(tmp_path):
    source = tmp_path / "employees.csv"
    source.write_text("employee_id,state\n1,SP\n2,RJ\n", encoding="utf-8")

    report = infer_csv(source, sample_size=1)

    assert report["rows_sampled"] == 1
    assert report["columns"][0]["semantic"] == "Identifier (ID)"


def test_uses_sampled_values_for_an_opaque_csv_column(tmp_path):
    source = tmp_path / "locations.csv"
    source.write_text("f27\nSP\nRJ\nMG\nBA\n", encoding="utf-8")

    report = infer_csv(source, sample_size=4)

    assert report["columns"][0]["semantic"] == "Geographic Location"


def test_limits_the_csv_sample_and_summarizes_semantics(tmp_path):
    source = tmp_path / "employees.csv"
    source.write_text("employee_id\n1\n2\n3\n", encoding="utf-8")

    report = infer_csv(source, sample_size=2)

    assert report["rows_sampled"] == 2
    assert report["summary"] == {"Identifier (ID)": 1}


@pytest.mark.parametrize("sample_size", [0, -1])
def test_rejects_non_positive_sample_sizes(tmp_path, sample_size):
    source = tmp_path / "employees.csv"
    source.write_text("employee_id\n1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="sample_size"):
        infer_csv(source, sample_size=sample_size)


def test_rejects_an_empty_csv(tmp_path):
    source = tmp_path / "empty.csv"
    source.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="header"):
        infer_csv(source)
