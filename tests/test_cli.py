import json

from colsemantics.cli import main


def test_cli_writes_a_json_report(tmp_path):
    source = tmp_path / "columns.csv"
    output = tmp_path / "report.json"
    source.write_text("employee_id\n1\n", encoding="utf-8")

    assert main(["infer", str(source), "--output", str(output)]) == 0

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["source"]["path"] == str(source)
    assert report["columns"][0]["semantic"] == "Identifier (ID)"


def test_cli_returns_an_input_error_for_an_unknown_profile(tmp_path, capsys):
    source = tmp_path / "columns.csv"
    output = tmp_path / "report.json"
    source.write_text("employee_id\n1\n", encoding="utf-8")

    assert main(["infer", str(source), "--profile", "en-US", "--output", str(output)]) == 2

    assert "Unknown profile" in capsys.readouterr().err
