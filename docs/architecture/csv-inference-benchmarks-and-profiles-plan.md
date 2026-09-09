# CSV Inference, Benchmarks, and Profiles Implementation Plan

**Goal:** Add deterministic CSV inference, named vocabulary profiles, and measurable benchmark tooling without new runtime dependencies.

**Architecture:** `profiles.py` owns immutable named contexts and optional YAML extensions. `csv_inference.py` turns a bounded CSV sample into the existing public inference inputs, while `cli.py` is only an argument parser and serializer. `benchmark.py` evaluates declarative JSON fixtures against the public API; the benchmark corpus remains separate from the wheel.

**Tech Stack:** Python 3.10+, standard-library `argparse`, `csv`, `json`, pytest, Ruff, mypy, PyYAML.

**Spec:** `docs/architecture/csv-inference-benchmarks-and-profiles.md`

## Global Constraints

- CSV is the only supported file format in this release; do not add pandas, PyArrow, or Parquet support.
- Preserve the existing `infer_column` and `infer_table` result contract.
- `pt-BR` is the embedded default profile and external YAML extends, never mutates, its context.
- Synthetic benchmark fixtures are versioned and run in CI; public corpora are manifest-only.
- All user-facing API, CLI, report keys, errors, and documentation are English.

## File Structure

- Create `src/colsemantics/profiles.py`: profile registry and scoped context loader.
- Create `src/colsemantics/csv_inference.py`: CSV sampling, content profiles, and report assembly.
- Create `src/colsemantics/cli.py`: `colsemantics infer` parser, errors, and JSON output.
- Create `src/colsemantics/benchmark.py`: fixture loading, evaluation, and metric aggregation.
- Create `benchmarks/synthetic.json`: small versioned cases for `pt-BR`.
- Create `benchmarks/public-corpora.json`: source-only public corpus manifest.
- Modify `src/colsemantics/__init__.py`, `pyproject.toml`, `README.md`, and `tests/test_colsemantics.py`.
- Create focused `tests/test_profiles.py`, `tests/test_csv_inference.py`, `tests/test_cli.py`, and `tests/test_benchmark.py`.

### Task 1: Add named, composable vocabulary profiles

**Files:**
- Create: `src/colsemantics/profiles.py`
- Modify: `src/colsemantics/__init__.py`
- Test: `tests/test_profiles.py`

**Interfaces:**
- Produces `available_profiles() -> tuple[str, ...]`.
- Produces `load_profile(name: str = "pt-BR", vocabulary_paths: str | None = None) -> SemanticContext`.
- Produces `temporary_profile(name: str = "pt-BR", vocabulary_paths: str | None = None) -> Iterator[None]`.

- [ ] Write failing tests for the default profile and an actionable unknown-profile error.

```python
def test_loads_the_embedded_portuguese_profile():
    assert available_profiles() == ("pt-BR",)
    assert load_profile().strong_categories


def test_unknown_profile_lists_available_profiles():
    with pytest.raises(ValueError, match="pt-BR"):
        load_profile("en-US")
```

- [ ] Run `pytest tests/test_profiles.py -v`; expect import failure because `profiles.py` does not exist.
- [ ] Implement a registry mapping `"pt-BR"` to `create_context()` and validate names before calling `load_vocabularies(vocabulary_paths, base_context)`.

```python
def load_profile(name: str = "pt-BR", vocabulary_paths: str | None = None) -> SemanticContext:
    try:
        base_context = _PROFILES[name]
    except KeyError as error:
        available = ", ".join(available_profiles())
        raise ValueError(f"Unknown profile '{name}'. Available profiles: {available}.") from error
    return load_vocabularies(vocabulary_paths, base_context)
```

- [ ] Add a test proving a YAML override affects only the scoped profile context and leaves the default context unchanged.
- [ ] Run `pytest tests/test_profiles.py -q` and `mypy`.
- [ ] Commit with `feat: add vocabulary profiles`.

### Task 2: Build a deterministic CSV inference service

**Files:**
- Create: `src/colsemantics/csv_inference.py`
- Test: `tests/test_csv_inference.py`

**Interfaces:**
- Produces `infer_csv(path: str | Path, *, sample_size: int = 10000, profile_name: str = "pt-BR", vocabulary_paths: str | None = None, encoding: str = "utf-8") -> dict[str, object]`.
- Report keys: `source`, `profile`, `sample_size`, `rows_sampled`, `columns`, and `summary`.

- [ ] Write a failing test using a small UTF-8 CSV fixture.

```python
def test_infers_csv_columns_from_a_bounded_sample(tmp_path):
    source = tmp_path / "employees.csv"
    source.write_text("employee_id,state\n1,SP\n2,RJ\n", encoding="utf-8")
    report = infer_csv(source, sample_size=1)
    assert report["rows_sampled"] == 1
    assert report["columns"][0]["semantic"] == "Identifier (ID)"
```

- [ ] Run `pytest tests/test_csv_inference.py::test_infers_csv_columns_from_a_bounded_sample -v`; expect import failure.
- [ ] Implement standard-library `csv.DictReader` handling. Read at most `sample_size` rows, reject zero or negative samples, reject headerless files, and create one `ContentProfile` per field with distinct values, count, uniqueness ratio, and mean string length when values are present.
- [ ] Add tests for sample limiting, missing input, empty file, invalid sample size, and a report summary that counts semantic labels.
- [ ] Run `pytest tests/test_csv_inference.py -q`.
- [ ] Commit with `feat: infer CSV files`.

### Task 3: Expose the CSV service through a dependency-free CLI

**Files:**
- Create: `src/colsemantics/cli.py`
- Modify: `pyproject.toml`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces console script `colsemantics` through `[project.scripts]`.
- Supports `colsemantics infer INPUT --profile pt-BR --sample 10000 --output report.json`.
- `main(argv: Sequence[str] | None = None) -> int` returns `0` on success and `2` for input errors.

- [ ] Write a failing test that invokes `main([...])`, reads the JSON output, and checks `report["source"]["path"]`.

```python
def test_cli_writes_a_json_report(tmp_path):
    source = tmp_path / "columns.csv"
    output = tmp_path / "report.json"
    source.write_text("employee_id\n1\n", encoding="utf-8")
    assert main(["infer", str(source), "--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["columns"][0]["semantic"] == "Identifier (ID)"
```

- [ ] Run the targeted test; expect import failure because `cli.py` does not exist.
- [ ] Implement an `argparse` command hierarchy with `infer` only. Delegate file work to `infer_csv`; serialize with `json.dump(..., ensure_ascii=False, indent=2)`. Catch `OSError`, `UnicodeError`, `csv.Error`, and `ValueError`, print `error: <message>` to stderr, and return `2`.
- [ ] Add `[project.scripts] colsemantics = "colsemantics.cli:main"` and tests for unknown profiles and invalid samples.
- [ ] Run `pytest tests/test_cli.py -q`, `ruff check .`, and `mypy`.
- [ ] Commit with `feat: add CSV inference CLI`.

### Task 4: Add synthetic benchmark evaluation and public corpus metadata

**Files:**
- Create: `src/colsemantics/benchmark.py`
- Modify: `src/colsemantics/cli.py`
- Create: `benchmarks/synthetic.json`
- Create: `benchmarks/public-corpora.json`
- Test: `tests/test_benchmark.py`

**Interfaces:**
- Produces `evaluate_cases(cases: Sequence[Mapping[str, object]]) -> dict[str, object]`.
- Produces `load_cases(path: str | Path) -> list[dict[str, object]]`.
- Report keys: `total_cases`, `semantic_accuracy`, `role_accuracy`, `domain_accuracy`, `coverage`, `by_profile`, and `confusion_matrix`.
- Adds `colsemantics benchmark CASES --output report.json` for local synthetic fixtures and deliberately does not download public corpora.

- [ ] Write a failing test for a two-case fixture that expects exact semantic accuracy and coverage.

```python
def test_reports_accuracy_coverage_and_confusion_matrix():
    report = evaluate_cases([
        {"profile": "pt-BR", "column_name": "employee_id", "expected_semantic": "Identifier (ID)"},
        {"profile": "pt-BR", "column_name": "unknown", "expected_semantic": "Generic / Unmapped"},
    ])
    assert report["semantic_accuracy"] == 1.0
    assert report["coverage"] == 0.5
```

- [ ] Run the targeted test; expect import failure because `benchmark.py` does not exist.
- [ ] Implement fixture validation, inference through the public API inside `temporary_profile`, and metric aggregation. Only compare role or domain when their expected field exists; record mismatches in `confusion_matrix[expected][actual]`.
- [ ] Add at least eight synthetic cases covering identifier, date, location from values, status from values, organizational domain, finance domain, free-form text, and generic fallback. Add one public-corpus manifest record with `name`, `source_url`, `license`, `sha256`, and `adapter`.
- [ ] Add tests for malformed fixtures and profile-specific aggregation.
- [ ] Add a CLI test for `benchmark` that writes the same JSON report returned by `evaluate_cases`.
- [ ] Run `pytest tests/test_benchmark.py -q`.
- [ ] Commit with `test: add semantic inference benchmarks`.

### Task 5: Document and verify the integrated release candidate

**Files:**
- Modify: `README.md`
- Modify: `src/colsemantics/__init__.py`
- Test: `tests/test_colsemantics.py`

**Interfaces:**
- Public exports include `available_profiles`, `load_profile`, `temporary_profile`, and `infer_csv`.
- README shows the CSV command, profile selection, YAML extension, and benchmark invocation without claiming Parquet support.

- [ ] Write failing public-export tests.

```python
def test_public_api_exports_csv_and_profile_interfaces():
    assert {"available_profiles", "infer_csv", "load_profile", "temporary_profile"} <= set(
        colsemantics.__all__
    )
```

- [ ] Run the targeted test; expect missing exports.
- [ ] Export the completed interfaces from `__init__.py` and update README examples to use `colsemantics infer employees.csv --profile pt-BR --sample 10000 --output report.json`.
- [ ] Run the full verification set:

```bash
python -m pytest -q
python -m ruff check .
python -m mypy
python -m build
git diff --check
```

- [ ] Install the generated wheel in a temporary virtual environment and run `colsemantics infer` against a temporary CSV fixture.
- [ ] Commit with `docs: document CSV inference workflow`.
