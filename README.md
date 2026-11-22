# colsemantics

[![PyPI version](https://img.shields.io/pypi/v/colsemantics)](https://pypi.org/project/colsemantics/)
[![Python versions](https://img.shields.io/pypi/pyversions/colsemantics)](https://pypi.org/project/colsemantics/)
[![CI](https://github.com/Caio-Analytics/colsemantics/actions/workflows/ci.yml/badge.svg)](https://github.com/Caio-Analytics/colsemantics/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/Caio-Analytics/colsemantics)](LICENSE)
[![PyPI downloads](https://img.shields.io/pypi/dm/colsemantics)](https://pypi.org/project/colsemantics/)

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

`pt-BR` is the embedded (and default) profile. A profile controls the column-name vocabulary only; value patterns such as e-mail, phone, and postal code are detected independently of it. Use `available_profiles()` to list embedded profiles and `load_profile()` when an application needs an explicit context.

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

The report includes semantic, role, and domain accuracy, coverage, per-profile metrics, a confusion matrix, and calibration buckets with expected calibration error. Public corpus definitions are stored as source manifests; they are not bundled or downloaded automatically.

## Confidence and review decisions

`raw_confidence` is the direct score assembled from independent evidence. `confidence` is the profile calibration for that score bucket, derived from the versioned calibration fixture. A result sets `review_required` when calibrated confidence is below `0.80`.

See `benchmarks/README.md` for the held-out validation set; its first measurement was 71% semantic accuracy on 52 hand-written cases (Brazilian and US column names), which shows the engine is not yet production-grade for English column names.

The embedded calibration is provisional: it is a controlled regression fixture, not evidence of production-grade accuracy. A held-out, versioned corpus is required before treating its precision as a production measurement.

## Value patterns and locales

When a column has sampled values, colsemantics also looks at how the values are written. Detection uses values only, so it works the same for Brazilian and US data and does not depend on the vocabulary profile.

| Type | Brazil (BR) | United States (US) |
|---|---|---|
| `phone` | `(11) 91234-5678`, `11 91234-5678`, `+55 11 91234-5678`, `(21) 3456-7890`, `0800 123 4567`; the area code (DDD) must exist, mobiles start with 9, landlines with 2-5 | `(415) 555-2671`, `415-555-2671`, `415.555.2671`, `+1 415 555 2671`; area code and exchange start with 2-9 and are not N11 |
| `postal_code` | CEP `01310-100` | `94105-1234` (ZIP+4) |
| `address` | `Rua das Flores, 123`, `Av. Paulista, 1578`, `Rodovia BR-101 km 5` | `123 Main St`, `500 N. Michigan Ave., Suite 300`, `PO Box 1234` |
| national id | `cpf`, `cnpj` (check digits verified) | `ssn` (area/group/serial ranges verified), `ein` (format only) |
| any | `email`, `uuid` | |

Bare digit strings such as `4155552671` or `11912345678`, and plain five-digit ZIP codes, are not reported as phones or postal codes because they are indistinguishable from ids and amounts. Addresses are matched heuristically and are never marked `validated`.

The result carries a `pattern` that says what was found and where it looks like it comes from:

```python
result = infer_column("f6", profile=profile_values(["(11) 91234-5678", "(21) 99876-5432"]))
result["pattern"]
# {"type": "phone", "locale": "BR", "variant": "mobile", "format": "(DD) 9NNNN-NNNN",
#  "coverage": 1.0, "validated": True,
#  "message": "100% of sampled values look like a Brazilian mobile phone number (e.g. (DD) 9NNNN-NNNN)"}
```

`pattern` is `None` when no format reaches its coverage threshold (80% of the sampled values, 60% for addresses). The same text is used as the `evidence` of the classification. You can still pass `detected_pattern="phone"` to `infer_column`; legacy names (`CPF`, `E-mail`, `Telefone`, `CEP`) keep working.

`infer_csv` reads each file with type detection (numbers, dates, booleans in Brazilian and US formats), picks the `,`, `;`, tab, or `|` delimiter from the header, samples rows uniformly with a seed, and reports duplicate headers and malformed rows in `warnings`.

## Sensitive-data recommendations

Each result includes a descriptive `sensitivity` recommendation. It does not modify input data.

- Validated CPF or SSN patterns: `high` / `mask`
- Detected street addresses: `high` / `mask`
- Person identity semantics: `high` / `restrict`
- Contact semantics (e-mail, phone): `high` / `mask`
- CNPJ, EIN, postal codes, other identifiers: `medium` / `review`
- Everything else: `none` / `allow`

## Result shape

```python
{
    "semantic": str,
    "role": str | None,
    "domain": str | None,
    "raw_confidence": float,
    "confidence": float,
    "evidence": str,
    "conclusive": bool,
    "review_required": bool,
    "sensitivity": {"level": str, "action": str, "reason": str},
    "pattern": dict | None,  # see "Value patterns and locales"
    "hypotheses": list[dict],
}
```

## Migrating from 0.2

`normalizar` and `tokenizar` were renamed to `normalize` and `tokenize`. The old names still work but emit a `DeprecationWarning` and will be removed in 1.0. `infer_table`, `assess_sensitivity`, `calibrate`, and `requires_review` are now listed in `__all__`.

Python 3.10 is no longer supported (it reached end of life, and current `rapidfuzz` requires 3.11).

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, checks, and the release process, and [CHANGELOG.md](CHANGELOG.md) for version history.

```bash
python -m pip install -e '.[dev]'
pytest --cov
ruff check .
ruff format --check .
mypy
```

## License

MIT.
