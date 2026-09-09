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

## Analyze a CSV file

Install the command-line interface with the package, then create a JSON report from a bounded CSV sample:

```bash
colsemantics infer employees.csv --profile pt-BR --sample 10000 --output report.json
```

CSV is the supported file format in this release. The report records its source, profile, sample size, inferred columns, and a semantic summary.

## Use sampled values

```python
from colsemantics import ContentProfile, infer_column

profile = ContentProfile(
    data_type="Text",
    distinct_values=["SP", "RJ", "MG", "BA"],
    distinct_count=4,
    uniqueness_ratio=0.1,
)

result = infer_column("f27", profile=profile)
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

## Vocabulary profiles and extensions

`pt-BR` is the embedded profile. Use `available_profiles()` to list embedded profiles and `load_profile()` when an application needs an explicit context.

```python
from colsemantics import infer_column, temporary_profile

with temporary_profile("pt-BR", "company-vocabulary.yaml"):
    result = infer_column("cost_bucket")
```

YAML extensions use the English schema and apply only within the selected context:

Provide one or more comma-separated YAML files to `load_vocabularies`, then use the returned context for the current operation.

```yaml
strong_categories:
  Project domain:
    - workstream
column_overrides:
  cost_bucket: Finance / Cost
```

Custom vocabularies are scoped with `ContextVar`, so separate concurrent analyses do not share vocabulary changes.

## Benchmark inference quality

Run the synthetic benchmark fixture included with the repository:

```bash
colsemantics benchmark benchmarks/synthetic.json --output benchmark-report.json
```

The report includes semantic, role, and domain accuracy, coverage, per-profile metrics, and a confusion matrix. Public corpus definitions are stored as source manifests; they are not bundled or downloaded automatically.

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
