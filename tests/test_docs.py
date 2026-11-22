"""Keep the documentation honest: examples run, and docs match the code."""

import runpy
from pathlib import Path

import colsemantics
from colsemantics import infer_csv

ROOT = Path(__file__).parents[1]


def _quickstart_output(capsys) -> str:
    runpy.run_path(str(ROOT / "examples" / "quickstart.py"), run_name="__main__")
    return capsys.readouterr().out


def test_readme_demo_matches_the_real_quickstart_output(capsys):
    output = _quickstart_output(capsys)
    brazilian_block = output.split("\ncustomers_us.csv")[0].strip()

    assert brazilian_block in (ROOT / "README.md").read_text(encoding="utf-8")


def test_sample_files_are_classified_as_documented():
    brazil = {
        c["column_name"]: c for c in infer_csv(ROOT / "examples" / "customers_br.csv")["columns"]
    }
    us = {c["column_name"]: c for c in infer_csv(ROOT / "examples" / "customers_us.csv")["columns"]}

    assert brazil["cpf"]["pattern"]["type"] == "cpf"
    assert brazil["telefone"]["pattern"]["locale"] == "BR"
    assert us["ssn"]["pattern"]["type"] == "ssn"
    assert us["phone_number"]["pattern"]["locale"] == "US"
    assert us["state"]["semantic"] == "Geographic Location"
    assert all(c["pattern"] is None or c["pattern"]["validated"] or c["pattern"]["type"] == "address"
               for c in brazil.values())  # fmt: skip


def test_every_public_name_is_in_the_api_reference():
    reference = (ROOT / "docs" / "api.md").read_text(encoding="utf-8")

    missing = [name for name in colsemantics.__all__ if name not in reference]
    assert missing == []


def test_public_api_has_docstrings():
    undocumented = [
        name
        for name in colsemantics.__all__
        if not (getattr(colsemantics, name).__doc__ or "").strip()
        or (getattr(colsemantics, name).__doc__ or "").startswith(f"{name}(")
    ]
    assert undocumented == []


def test_versions_agree():
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert f'version = "{colsemantics.__version__}"' in pyproject
    assert f"version: {colsemantics.__version__}" in citation
    assert f"## [{colsemantics.__version__}]" in (ROOT / "CHANGELOG.md").read_text("utf-8")


def test_readme_links_point_to_existing_files():
    import re

    prefix = "https://github.com/Caio-Analytics/colsemantics/blob/main/"
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    targets = re.findall(r"\]\((" + re.escape(prefix) + r"[^)#]+)", text)

    assert targets
    assert [t for t in targets if not (ROOT / t.removeprefix(prefix)).exists()] == []
    assert not re.search(r"\]\((?!http|#|mailto:)", text), "use absolute links so PyPI renders them"
