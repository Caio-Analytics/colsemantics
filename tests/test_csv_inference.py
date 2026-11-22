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


def test_report_names_each_column(tmp_path):
    source = tmp_path / "employees.csv"
    source.write_text("employee_id,state\n1,SP\n", encoding="utf-8")

    report = infer_csv(source)

    assert [(c["column_index"], c["column_name"]) for c in report["columns"]] == [
        (0, "employee_id"),
        (1, "state"),
    ]


def test_detects_semicolon_delimited_files(tmp_path):
    source = tmp_path / "employees.csv"
    source.write_text("employee_id;state\n1;SP\n", encoding="utf-8")

    report = infer_csv(source)

    assert report["source"]["delimiter"] == ";"
    assert [c["column_name"] for c in report["columns"]] == ["employee_id", "state"]


def test_explicit_delimiter_overrides_detection(tmp_path):
    source = tmp_path / "employees.csv"
    source.write_text("a|b;c\n1|2;3\n", encoding="utf-8")

    report = infer_csv(source, delimiter="|")

    assert [c["column_name"] for c in report["columns"]] == ["a", "b;c"]


def test_rejects_multi_character_delimiters(tmp_path):
    source = tmp_path / "employees.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="delimiter"):
        infer_csv(source, delimiter="||")


def test_strips_a_utf8_bom_from_the_first_header(tmp_path):
    source = tmp_path / "employees.csv"
    source.write_bytes("﻿employee_id\n1\n".encode())

    report = infer_csv(source)

    assert report["columns"][0]["column_name"] == "employee_id"


def test_explains_how_to_fix_an_encoding_error(tmp_path):
    source = tmp_path / "employees.csv"
    source.write_bytes("nome\nJoão\n".encode("latin-1"))

    with pytest.raises(ValueError, match="latin-1"):
        infer_csv(source)
    assert infer_csv(source, encoding="latin-1")["rows_sampled"] == 1


def test_detects_cpf_values_and_marks_them_sensitive(tmp_path):
    source = tmp_path / "people.csv"
    source.write_text("doc\n529.982.247-25\n111.444.777-35\n", encoding="utf-8")

    column = infer_csv(source)["columns"][0]

    assert column["sensitivity"] == {
        "level": "high",
        "action": "mask",
        "reason": "validated CPF pattern",
    }


def test_analyzes_duplicate_headers_separately_and_warns(tmp_path):
    source = tmp_path / "dupes.csv"
    source.write_text("code,code\nSP,1\nRJ,2\n", encoding="utf-8")

    report = infer_csv(source)

    assert [c["column_index"] for c in report["columns"]] == [0, 1]
    assert any("'code' appears in columns 0, 1" in warning for warning in report["warnings"])


def test_duplicate_headers_do_not_share_values(tmp_path):
    source = tmp_path / "dupes.csv"
    source.write_text("f27,f27\nSP,x1\nRJ,x2\nMG,x3\nBA,x4\n", encoding="utf-8")

    first, second = infer_csv(source)["columns"]

    assert first["semantic"] == "Geographic Location"
    assert second["semantic"] != "Geographic Location"


def test_reports_ragged_rows_instead_of_hiding_them(tmp_path):
    source = tmp_path / "ragged.csv"
    source.write_text("id,name\n1\n2,b,extra\n3,c\n\n", encoding="utf-8")

    report = infer_csv(source)

    assert report["rows_sampled"] == 3
    assert report["rows_malformed"] == 2
    assert any("2 sampled row(s)" in warning for warning in report["warnings"])


def test_clean_files_report_no_warnings(tmp_path):
    source = tmp_path / "clean.csv"
    source.write_text("id,name\n1,a\n", encoding="utf-8")

    report = infer_csv(source)

    assert report["warnings"] == []
    assert report["rows_malformed"] == 0


def _write_sorted_file(tmp_path, rows=300):
    source = tmp_path / "sorted.csv"
    lines = ["kind,amount"] + [f"{'A' if i < rows // 2 else 'B'},{i}" for i in range(rows)]
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return source


def test_reservoir_sampling_covers_the_whole_file(tmp_path):
    source = _write_sorted_file(tmp_path)

    report = infer_csv(source, sample_size=50)

    assert report["sampling"] == "reservoir"
    assert report["rows_read"] == 300
    assert report["rows_sampled"] == 50


def test_head_sampling_stops_early_and_is_biased_by_order(tmp_path):
    source = _write_sorted_file(tmp_path)

    report = infer_csv(source, sample_size=50, sampling="head")

    assert report["rows_sampled"] == 50
    assert report["rows_read"] == 50


def test_reservoir_sampling_is_reproducible_per_seed(tmp_path):
    source = _write_sorted_file(tmp_path)

    first = infer_csv(source, sample_size=20, seed=7)
    second = infer_csv(source, sample_size=20, seed=7)

    assert first == second


def test_rejects_unknown_sampling_modes(tmp_path):
    source = _write_sorted_file(tmp_path, rows=4)

    with pytest.raises(ValueError, match="sampling"):
        infer_csv(source, sampling="tail")  # type: ignore[arg-type]


def test_numeric_csv_columns_use_numeric_evidence(tmp_path):
    source = tmp_path / "ids.csv"
    source.write_text("f1\n" + "\n".join(str(n) for n in range(1, 60)) + "\n", encoding="utf-8")

    assert infer_csv(source, sample_size=100)["columns"][0]["semantic"] == "Identifier (ID)"
