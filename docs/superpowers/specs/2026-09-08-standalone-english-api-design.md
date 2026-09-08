# Standalone English API design

## Goal

Release colsemantics 0.3.0 as a standalone English-language Python library. The release removes the Portuguese API, result schema, taxonomy labels, YAML schema, and internal messages.

## Public API

The package exports only the English public interface:

```python
from colsemantics import ContentProfile, infer_column, infer_table
```

`ContentProfile` accepts:

- `data_type`
- `distinct_values`
- `distinct_count`
- `uniqueness_ratio`
- `mean_string_length`
- `fixed_length`
- `skewness`
- `minimum`
- `monotonically_increasing`
- `fixed_decimal_places`

`infer_column(column_name, detected_pattern="None", profile=None)` returns:

```python
{
    "semantic": str,
    "role": str | None,
    "domain": str | None,
    "confidence": float,
    "evidence": str,
    "conclusive": bool,
    "hypotheses": list[dict],
}
```

`infer_table(columns)` accepts dictionaries with `column_name`, optional `detected_pattern`, and optional `profile`. It returns the same English result shape for each input column.

No Portuguese aliases, keys, dataclasses, or helper functions remain public.

## Taxonomy and detection

All category labels, axes, constant names, detector messages, and vocabulary data use English. The supported Portuguese and English source tokens remain part of the vocabulary because they are data inputs, not public API.

The classifier continues to combine structured patterns, strong tokens, fuzzy matches, gazetteers, structural signatures, and table context. This release changes names and contracts, not inference rules or confidence weighting.

## Vocabulary configuration

Vocabulary YAML remains English-only:

```yaml
strong_categories:
  Project domain:
    - workstream
fuzzy_categories: {}
gazetteers:
  - name: project status
    values: [planned, active, closed]
    category: Status / Indicator / Flag
    axis: role
column_overrides:
  cost_bucket: Finance / Cost
```

The loader validates axes as `role` or `domain`, validates category and value types, and returns actionable errors for invalid files.

## Compatibility and versioning

This is an intentional breaking release. Existing code using Portuguese names or result fields must migrate to the English API. The project is pre-1.0 and has no reported users, so no compatibility layer or deprecation period is included.

`pyproject.toml` and `__version__` both become `0.3.0`.

## Documentation and release

The README documents only the standalone package and its English API. It contains no reference to Recon or to extraction history.

After validation, create a GitHub release named `v0.3.0`. The existing Trusted Publishing workflow publishes the package to PyPI.

## Verification

- Rewrite tests against the English public API and result shape.
- Add coverage for YAML axis validation and invalid YAML structures.
- Run pytest, Ruff, mypy, package build, and `git diff --check`.
- Install the built wheel in an isolated environment and run a short import and inference smoke test.
