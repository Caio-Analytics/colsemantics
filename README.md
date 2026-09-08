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
print(result["papel"])
```

The package keeps the original Portuguese category labels for compatibility with Recon, the project it was extracted from.

## Use sampled values

```python
from colsemantics import PerfilConteudo, infer_column

profile = PerfilConteudo(
    tipo_dados="Texto",
    valores_distintos=["SP", "RJ", "MG", "BA"],
    n_unicos=4,
    ratio_unicidade=0.1,
)

result = infer_column("f27", perfil=profile)
print(result["dominio"])
```

## Analyze a table

```python
from colsemantics import infer_table

results = infer_table(
    [
        {"nome": "employee_id"},
        {"nome": "department_name"},
        {"nome": "start_date"},
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
    "semantica": str,
    "papel": str | None,
    "dominio": str | None,
    "confianca_score": float,
    "origem": str,
    "conclusiva": bool,
    "hipoteses": list[dict],
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

MIT. The semantic inference engine was extracted from [Recon](https://github.com/Caio-Analytics/Recon).
