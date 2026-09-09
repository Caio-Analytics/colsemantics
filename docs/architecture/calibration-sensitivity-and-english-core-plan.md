# Calibration, Sensitivity, and English Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver empirically calibrated confidence, a deterministic sensitive-data policy, and an English-only inference core.

**Architecture:** First replace the Portuguese internal taxonomy, evidence, detector, context, vocabulary, and inference contracts with equivalent English contracts while keeping the `pt-BR` terms as profile data. Then add pure calibration and sensitivity modules around the normalized English result. Finally, extend benchmark reporting and documentation to make confidence evidence visible.

**Tech Stack:** Python 3.10+, pytest, Ruff, mypy, standard-library JSON and dataclasses.

**Spec:** `docs/architecture/calibration-sensitivity-and-english-core.md`

## Global Constraints

- Preserve detector ordering and numeric weights during the English-core refactor.
- Keep Portuguese only as `pt-BR` vocabulary data, never as code identifiers, mapping keys, output fields, errors, or evidence messages.
- Keep `raw_confidence` as the unchanged noisy-OR score; make `confidence` the calibrated score.
- Use lower-inclusive 0.10 raw-score buckets and a `0.80` review threshold.
- Do not transform source data; `sensitivity` only recommends `allow`, `review`, `mask`, or `restrict`.
- Keep calibration explicit and versioned; inference never learns from runtime inputs.

## File Structure

- Create `src/colsemantics/calibration.py`: bucket selection, calibration table loading, and calibrated-score lookup.
- Create `src/colsemantics/sensitivity.py`: policy rules and the public sensitivity object.
- Modify `src/colsemantics/_taxonomy.py`, `evidence.py`, `detectors.py`, `context.py`, `vocabulary.py`, `vocabularies.py`, `tokens.py`, and `__init__.py`: English-only core names and contracts.
- Modify `src/colsemantics/benchmark.py`: calibration records, expected calibration error, and per-profile reports.
- Create `benchmarks/calibration.json`: versioned `pt-BR` calibration table derived from fixtures.
- Modify `benchmarks/synthetic.json`, `README.md`, and tests.
- Create `tests/test_calibration.py` and `tests/test_sensitivity.py`.

### Task 1: Lock current classifications before renaming the core

**Files:**
- Modify: `tests/test_colsemantics.py`
- Test: `tests/test_colsemantics.py`

**Interfaces:**
- Records English public results for identifier, date, geographic values, status values, organizational domain, finance domain, free-form text, and generic fallback.

- [ ] Write a regression parametrization that captures semantic, role, domain, and raw confidence for representative inputs.

```python
@pytest.mark.parametrize(
    ("column_name", "expected_semantic"),
    [
        ("employee_id", "Identifier (ID)"),
        ("department_name", "Organizational Structure"),
        ("xyzabc123", "Generic / Unmapped"),
    ],
)
def test_english_core_regression_cases(column_name, expected_semantic):
    assert infer_column(column_name)["semantic"] == expected_semantic
```

- [ ] Run the targeted test and confirm it passes against the current public wrapper.
- [ ] Add value-profile regression cases for Brazilian state codes and status values, preserving their expected English results.
- [ ] Run `pytest tests/test_colsemantics.py -q`.
- [ ] Commit with `test: lock semantic inference regressions`.

### Task 2: Translate the inference core at its source

**Files:**
- Modify: `src/colsemantics/_taxonomy.py`
- Modify: `src/colsemantics/evidence.py`
- Modify: `src/colsemantics/detectors.py`
- Modify: `src/colsemantics/context.py`
- Modify: `src/colsemantics/vocabulary.py`
- Modify: `src/colsemantics/vocabularies.py`
- Modify: `src/colsemantics/tokens.py`
- Modify: `src/colsemantics/__init__.py`
- Test: `tests/test_colsemantics.py`

**Interfaces:**
- Produces `Evidence(category, axis, weight, source)`, `ROLE_AXIS`, `DOMAIN_AXIS`, `ContentProfile`, English result keys, and English category constants.
- Retains `pt-BR` terms as values in the profile vocabulary.

- [ ] Write a failing source-contract test that imports `Evidence` and checks its English dataclass fields.

```python
def test_evidence_uses_english_fields():
    evidence = Evidence("Identifier (ID)", "role", 0.9, "exact token 'id'")
    assert evidence.category == "Identifier (ID)"
```

- [ ] Run the targeted test; expect import failure for `Evidence` before the refactor.
- [ ] Rename taxonomy constants and category strings at their definition. Translate axes, evidence fields, ranking keys, detector names, context fields, vocabulary mapping keys, and token helpers. Replace evidence strings such as `conteúdo validado como` with English text while leaving `pt-BR` token values unchanged.
- [ ] Remove `_CATEGORY_LABELS`, `_legacy_profile`, and the translation boundary so `infer_column` and `infer_table` emit English results directly.
- [ ] Run `pytest -q`, `ruff check .`, and `mypy`; compare regression behavior from Task 1.
- [ ] Commit with `refactor: translate inference core to English`.

### Task 3: Add explicit calibration tables and review decisions

**Files:**
- Create: `src/colsemantics/calibration.py`
- Create: `benchmarks/calibration.json`
- Modify: `src/colsemantics/__init__.py`
- Test: `tests/test_calibration.py`

**Interfaces:**
- Produces `bucket_for(raw_confidence: float) -> str` using `0.0-0.1` through `0.9-1.0` lower-inclusive buckets.
- Produces `calibrate(raw_confidence: float, profile_name: str) -> float`.
- Produces `requires_review(confidence: float) -> bool` where `confidence < 0.80`.

- [ ] Write a failing bucket and threshold test.

```python
def test_calibration_uses_bucket_precision_and_review_threshold():
    assert bucket_for(0.83) == "0.8-0.9"
    assert calibrate(0.83, "pt-BR") == 0.88
    assert requires_review(0.79) is True
```

- [ ] Run the targeted test; expect import failure because `calibration.py` does not exist.
- [ ] Implement bucket validation for values in `[0.0, 1.0]`, load the immutable `pt-BR` table, use empirical precision for known buckets, and return the raw-score bucket midpoint for unknown buckets.
- [ ] Add tests for `0.0`, `1.0`, unknown profiles, and empty buckets. Add the `pt-BR` calibration fixture with bucket count, correct count, and precision.
- [ ] Integrate calibration after raw result assembly: rename the current score to `raw_confidence`, assign calibrated `confidence`, and add `review_required`.
- [ ] Run `pytest tests/test_calibration.py tests/test_colsemantics.py -q`.
- [ ] Commit with `feat: calibrate inference confidence`.

### Task 4: Add the deterministic sensitive-data policy

**Files:**
- Create: `src/colsemantics/sensitivity.py`
- Modify: `src/colsemantics/__init__.py`
- Test: `tests/test_sensitivity.py`

**Interfaces:**
- Produces `assess_sensitivity(semantic: str, detected_pattern: str) -> dict[str, str]`.
- Adds `sensitivity` with `level`, `action`, and `reason` to column and table results.

- [ ] Write failing policy-precedence tests.

```python
def test_validated_cpf_has_priority_over_generic_identifier():
    result = infer_column("field_1", detected_pattern="CPF")
    assert result["sensitivity"] == {
        "level": "high",
        "action": "mask",
        "reason": "validated CPF pattern",
    }
```

- [ ] Run the targeted test; expect missing `sensitivity`.
- [ ] Implement ordered rules for CPF, person identity, contact, generic identifier, and default no-match. Return only the three documented keys.
- [ ] Add tests for every rule, contact and person categories, identifier fallback, default allow, and a low-confidence non-sensitive result with `review_required` still true.
- [ ] Run `pytest tests/test_sensitivity.py -q`.
- [ ] Commit with `feat: add sensitive-data policy`.

### Task 5: Make calibration observable in benchmarks and documentation

**Files:**
- Modify: `src/colsemantics/benchmark.py`
- Modify: `src/colsemantics/cli.py`
- Modify: `README.md`
- Test: `tests/test_benchmark.py`

**Interfaces:**
- Benchmark reports `calibration` by profile with bucket counts, correct counts, precision, and expected calibration error.
- `colsemantics benchmark` writes the extended report unchanged through its existing output option.

- [ ] Write a failing benchmark assertion for a calibration bucket and expected calibration error.

```python
def test_benchmark_reports_calibration_by_profile():
    report = evaluate_cases([
        {
            "profile": "pt-BR",
            "column_name": "employee_id",
            "expected_semantic": "Identifier (ID)",
        }
    ])
    assert report["by_profile"]["pt-BR"]["calibration"]["0.8-0.9"]["count"] >= 1
    assert report["by_profile"]["pt-BR"]["expected_calibration_error"] >= 0.0
```

- [ ] Run the targeted test; expect missing calibration fields.
- [ ] Record raw confidence, calibrated confidence, review decision, predicted semantic, and expected semantic during evaluation. Aggregate each known expected semantic into calibration buckets and compute expected calibration error as `sum(abs(precision - bucket_midpoint) * count) / total`.
- [ ] Document calibrated confidence, the `0.80` review threshold, sensitivity policy, and the meaning of provisional synthetic calibration. Do not claim that the synthetic fixture proves production-grade calibration.
- [ ] Run the full verification set:

```bash
python -m pytest -q
python -m ruff check .
python -m mypy
python -m build
git diff --check
```

- [ ] Install the wheel in a temporary virtual environment; run `colsemantics infer` and `colsemantics benchmark`; assert `raw_confidence`, `sensitivity`, and calibration report fields.
- [ ] Commit with `docs: explain calibrated confidence and sensitivity`.
