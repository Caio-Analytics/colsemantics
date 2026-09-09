# Standalone English API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release colsemantics 0.3.0 as an English-only standalone library.

**Architecture:** Rename inference contracts at their source. Keep Portuguese source tokens as classifier input data, but expose only English types, labels, result keys, configuration, messages, and documentation.

**Tech Stack:** Python 3.10+, pytest, Ruff, mypy, RapidFuzz, PyYAML.

**Spec:** `docs/superpowers/specs/2026-09-08-standalone-english-api-design.md`

## Global Constraints

- Version metadata and runtime version must equal `0.3.0`.
- Public exports, categories, YAML keys, axes, messages, and result keys must be English-only.
- Keep detector weights and execution order unchanged.
- Pass pytest, Ruff, mypy, build, wheel smoke test, and `git diff --check`.

---

### Task 1: Translate the inference domain at its source

**Files:**
- Modify: `src/colsemantics/_taxonomy.py`
- Modify: `src/colsemantics/evidence.py`
- Modify: `src/colsemantics/detectors.py`
- Test: `tests/test_colsemantics.py`

**Interfaces:**
- Produces `ROLE_AXIS`, `DOMAIN_AXIS`, English category strings, and `ContentProfile`.

- [ ] Write a failing public result test.

```python
def test_identifier_uses_english_taxonomy():
    result = infer_column("employee_id")
    assert result["semantic"] == "Identifier (ID)"
    assert result["role"] == "Identifier (ID)"
```

- [ ] Run `.venv/bin/python -m pytest tests/test_colsemantics.py::test_identifier_uses_english_taxonomy -v`; it must fail before migration.
- [ ] Rename category constants, axis values, profile fields, detector messages, and evidence fields to English. Do not change weights.
- [ ] Run `.venv/bin/python -m pytest tests/test_colsemantics.py -q` and commit `refactor: translate semantic taxonomy to English`.

### Task 2: Make the English API the only contract

**Files:**
- Modify: `src/colsemantics/__init__.py`
- Modify: `src/colsemantics/tokens.py`
- Test: `tests/test_colsemantics.py`

**Interfaces:**
- Produces `infer_column(column_name, detected_pattern="None", profile=None)`.
- Produces `infer_table(columns)` with `column_name`, `detected_pattern`, and `profile` input keys.

- [ ] Write a failing result-shape test.

```python
def test_infer_column_returns_only_english_keys():
    result = infer_column("department_name")
    assert set(result) == {"semantic", "role", "domain", "confidence", "evidence", "conclusive", "hypotheses"}
```

- [ ] Run `.venv/bin/python -m pytest tests/test_colsemantics.py::test_infer_column_returns_only_english_keys -v`; it must fail before removing wrappers.
- [ ] Remove `inferir_semantica`, `inferir_semanticas_da_tabela`, `PerfilConteudo`, `semanticas_para_gap_analysis`, and result translation code. Emit English results directly.
- [ ] Run `.venv/bin/python -m pytest tests/test_colsemantics.py -q` and commit `feat!: make the English API the only public contract`.

### Task 3: Validate the English vocabulary schema

**Files:**
- Modify: `src/colsemantics/context.py`
- Modify: `src/colsemantics/vocabulary.py`
- Modify: `src/colsemantics/vocabularies.py`
- Test: `tests/test_colsemantics.py`

**Interfaces:**
- Accepts YAML `strong_categories`, `fuzzy_categories`, `gazetteers`, and `column_overrides`.
- Gazetteer axes are only `role` or `domain`.

- [ ] Write a failing invalid-axis test.

```python
def test_custom_gazetteer_rejects_an_invalid_axis(tmp_path):
    path = tmp_path / "vocabulary.yaml"
    path.write_text("gazetteers:\n  - name: status\n    values: [open]\n    category: Status / Indicator / Flag\n    axis: category\n")
    with pytest.raises(ValueError, match="axis"):
        load_vocabularies(str(path))
```

- [ ] Run the targeted pytest command and confirm failure.
- [ ] Rename mapping fields internally, validate axes against `{ROLE_AXIS, DOMAIN_AXIS}`, and produce actionable English errors.
- [ ] Run vocabulary tests and commit `feat: validate English vocabulary configuration`.

### Task 4: Prepare and verify the release candidate

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml`
- Modify: `src/colsemantics/__init__.py`
- Test: `tests/test_colsemantics.py`

- [ ] Add a failing runtime-version test asserting `__version__ == "0.3.0"`.
- [ ] Update the README to document only the final English API and YAML schema. Set both version declarations to `0.3.0`.
- [ ] Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy
.venv/bin/python -m build
git diff --check
```

- [ ] Install `dist/colsemantics-0.3.0-py3-none-any.whl` in `/tmp/colsemantics-wheel-test` and smoke-test `infer_column("employee_id")`.
- [ ] Commit `docs: prepare standalone English release`.
- [ ] Push and create `v0.3.0` only after the user approves the validated release candidate.
