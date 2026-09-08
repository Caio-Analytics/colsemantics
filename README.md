# colsemantics

`colsemantics` infers the structural role and business domain of tabular columns from column names, sampled values, and neighboring columns.

It is useful when a dataset has unclear headers such as `cd_dpto_lot`, `f27`, or `SUPPLIER_CONTACT_CODE`.

## Installation

```bash
pip install colsemantics
```

## Quick start

```python
from colsemantics import infer_column

result = infer_column("SUPPLIER_CONTACT_CODE")
print(result["role"])
```

The English API returns English field names and category labels.

## Use sampled values

```python
from colsemantics import ContentProfile, infer_column

profile = ContentProfile(
    data_type="Text",
    distinct_values=["SP", "RJ", "MG", "BA"],
    distinct_count=4,
    uniqueness_ratio=0.1,
)

result = infer_column("f27", perfil=profile)
print(result["domain"])
```

## Analyze a table

```python
from colsemantics import infer_table

results = infer_table(
    [
        {"column_name": "employee_id"},
        {"column_name": "department_name"},
        {"column_name": "start_date"},
    ]
)
```

`infer_table` uses high-confidence classifications as table context when it evaluates ambiguous columns.

## Customize a vocabulary

Provide one or more comma-separated YAML files to `load_vocabularies`, then use the returned context for the current operation.

```yaml
strong_categories:
  Project domain:
    - workstream
column_overrides:
  cost_bucket: Financeiro / Custo
```

```python
from colsemantics import infer_column, load_vocabularies
from colsemantics.context import reset_context, set_context

token = set_context(load_vocabularies("company-vocabulary.yaml"))
try:
    result = infer_column("cost_bucket")
finally:
    reset_context(token)
```

Custom vocabularies are scoped with `ContextVar`, so separate concurrent analyses do not share vocabulary changes.

## Result shape

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

## Development

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
mypy
```

## License

MIT.
