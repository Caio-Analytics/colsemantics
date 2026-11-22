# colsemantics

[![PyPI version](https://img.shields.io/pypi/v/colsemantics)](https://pypi.org/project/colsemantics/)
[![Python versions](https://img.shields.io/pypi/pyversions/colsemantics)](https://pypi.org/project/colsemantics/)
[![CI](https://github.com/Caio-Analytics/colsemantics/actions/workflows/ci.yml/badge.svg)](https://github.com/Caio-Analytics/colsemantics/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/Caio-Analytics/colsemantics)](https://github.com/Caio-Analytics/colsemantics/blob/main/LICENSE)
[![PyPI downloads](https://img.shields.io/pypi/dm/colsemantics)](https://pypi.org/project/colsemantics/)

**Find out what each column of a table means, and which ones hold personal data, without a schema.**
`colsemantics` infers the role (identifier, date, money, contact, ...), the business domain, and a
privacy recommendation for tabular columns, from names, sampled values, and neighboring columns.
It understands Brazilian and US formats (CPF, CNPJ, CEP, SSN, ZIP, phone numbers, addresses).

[Documentation](https://github.com/Caio-Analytics/colsemantics/blob/main/docs/README.md) · [Changelog](https://github.com/Caio-Analytics/colsemantics/blob/main/CHANGELOG.md) · [Contribuir / Contributing](https://github.com/Caio-Analytics/colsemantics/blob/main/CONTRIBUTING.md) · [Em português](#em-português)

```text
$ python examples/quickstart.py
customers_br.csv  (delimiter ';', 5 rows)
column          semantic                   sensitivity     pattern
nome            Person Name / Identifier   high/restrict   
cpf             Identifier (ID)            high/mask       BR cpf
telefone        Contact / Network          high/mask       BR phone
cep             Geographic Location        medium/review   BR postal_code
endereco        Geographic Location        high/mask       BR address
cidade          Geographic Location        none/allow      
dt_cadastro     Date / Calendar            none/allow      
valor_total     Financial Value            none/allow      
ativo           Status / Indicator / Flag  none/allow
```

Real output for [`examples/customers_br.csv`](https://github.com/Caio-Analytics/colsemantics/blob/main/examples/customers_br.csv). The US sample,
[`examples/customers_us.csv`](https://github.com/Caio-Analytics/colsemantics/blob/main/examples/customers_us.csv), is classified the same way (SSN, ZIP+4,
`(415) 555-2671`, `street_address`).

## When it helps

- **Personal-data scans (LGPD, GDPR, CCPA):** flag CPF, SSN, phones, e-mails, and addresses, and get a
  `mask`, `restrict`, or `review` recommendation for each column.
- **Data catalogs and onboarding:** label the columns of files that arrive with headers such as
  `cd_dpto_lot`, `f27`, or `SUPPLIER_CONTACT_CODE`.
- **ETL and schema mapping:** decide which column is the key, the date, the amount.
- **Triage:** every result says why (`evidence`) and whether a human should look (`review_required`).

## Installation

```bash
pip install colsemantics
```

Python 3.11 or newer. Dependencies: `rapidfuzz`, `unidecode`, `PyYAML`.

## Quick start

```python
from colsemantics import infer_column

result = infer_column("SUPPLIER_CONTACT_CODE")
print(result["semantic"], result["confidence"], result["evidence"])
```

Add sampled values and opaque names become classifiable:

```python
from colsemantics import infer_column
from colsemantics.profiling import profile_values

profile = profile_values(["SP", "RJ", "MG", "BA"])
print(infer_column("f27", profile=profile)["semantic"])  # Geographic Location

profile = profile_values(["(11) 91234-5678", "(21) 99876-5432"])
result = infer_column("f6", profile=profile)
print(result["pattern"]["message"])
# 100% of sampled values look like a Brazilian mobile phone number (e.g. (DD) 9NNNN-NNNN)
```

Classify a whole file (the delimiter, encoding, and column types are detected for you):

```bash
colsemantics infer employees.csv --output report.json
```

```python
from colsemantics import infer_csv, infer_table

report = infer_csv("employees.csv")  # dict with one result per column
results = infer_table([{"column_name": "employee_id"}, {"column_name": "start_date"}])
```

## What you get

Every result is a typed dictionary. This is the result for the phone column above (shortened):

```python
{
    "semantic": "Contact / Network",
    "role": "Contact / Network", "domain": None,
    "raw_confidence": 0.98, "confidence": 0.98,
    "evidence": "100% of sampled values look like a Brazilian mobile phone number (e.g. ...)",
    "conclusive": True, "review_required": False,
    "sensitivity": {"level": "high", "action": "mask", "reason": "contact semantic"},
    "pattern": {"type": "phone", "locale": "BR", "variant": "mobile", "coverage": 1.0, ...},
    "hypotheses": [...],   # ranked alternatives
}
```

Field-by-field reference: [docs/api.md](https://github.com/Caio-Analytics/colsemantics/blob/main/docs/api.md). Recognized formats and their limits:
[docs/patterns.md](https://github.com/Caio-Analytics/colsemantics/blob/main/docs/patterns.md).

| Detected | Recommendation |
|---|---|
| Validated CPF or SSN, street address | `high` / `mask` |
| Person name semantic | `high` / `restrict` |
| E-mail, phone | `high` / `mask` |
| CNPJ, EIN, postal code, coordinates, other identifiers | `medium` / `review` |
| Anything else | `none` / `allow` |

The recommendation is descriptive. colsemantics never modifies your data.

## Custom vocabularies

Extend the built-in vocabulary per analysis with YAML, scoped so concurrent analyses stay isolated:

```python
from colsemantics import infer_column, temporary_profile

with temporary_profile("pt-BR", "company-vocabulary.yaml"):
    result = infer_column("cost_bucket")
```

Schema and examples: [docs/vocabulary.md](https://github.com/Caio-Analytics/colsemantics/blob/main/docs/vocabulary.md).

## Accuracy and limits

Measured on hand-written and public-catalog benchmark sets (see [benchmarks/README.md](https://github.com/Caio-Analytics/colsemantics/blob/main/benchmarks/README.md)):

| Set | Accuracy |
|---|---|
| US public datasets, names plus values (360 columns, held out) | 98% |
| US public datasets, names only (390 columns, held out) | 69% |
| Hand-written Brazilian and US names (89 columns) | 99% |

- **The calibration is provisional.** `confidence` maps scores to precision measured on a small
  fixture, not on production data. Use `review_required` as a prompt for a human, not a guarantee.
- **Yes/no columns judged by name alone are weak (about 40%).** Names such as `Domestic` or `Safety`
  carry no signal. With sampled values they are recognized reliably.
- The benchmarks are small and partly synthetic. Treat them as regression checks, not as proof of
  accuracy on your data. Please open an issue with a column that was wrong.
- Brazilian and US formats only. Column-name vocabulary is Portuguese and English with some Spanish.

## How it compares

| Tool | Focus | colsemantics |
|---|---|---|
| `ydata-profiling`, `pandas-profiling` | Statistics and quality reports for a DataFrame | Infers *meaning* (role, domain, sensitivity), not distributions |
| Microsoft Presidio | Finds personal data inside text with recognizers and NLP | Works per *column*, adds business roles, no model downloads |
| Great Expectations, Pandera | Validate data against rules you write | Infers what to validate in the first place |
| Capital One `dataprofiler` | Model-based column labeling | Lightweight (three dependencies), explainable evidence, built-in Brazilian formats |

They solve neighboring problems and combine well. Check each project's documentation for its
current scope.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](https://github.com/Caio-Analytics/colsemantics/blob/main/CONTRIBUTING.md) for setup, checks, and the
release process, and [CHANGELOG.md](https://github.com/Caio-Analytics/colsemantics/blob/main/CHANGELOG.md) for version history.

```bash
python -m pip install -e '.[dev]'
pytest --cov
ruff check . && ruff format --check .
mypy
```

If you use colsemantics in research, cite it with [CITATION.cff](https://github.com/Caio-Analytics/colsemantics/blob/main/CITATION.cff).

## Em português

**`colsemantics` descobre o que cada coluna de uma tabela significa e quais colunas têm dados
pessoais, sem precisar de esquema.** Ele infere o papel (identificador, data, valor, contato, ...), o
domínio de negócio e uma recomendação de privacidade a partir dos nomes, de amostras de valores e
das colunas vizinhas. Reconhece formatos brasileiros e americanos: CPF, CNPJ, CEP, telefone com DDD
validado, endereço, SSN, ZIP e outros.

```bash
pip install colsemantics
colsemantics infer clientes.csv --output relatorio.json
```

```python
from colsemantics import infer_csv

relatorio = infer_csv("clientes.csv")  # detecta delimitador (;), encoding e tipos
for coluna in relatorio["columns"]:
    print(coluna["column_name"], coluna["semantic"], coluna["sensitivity"]["action"])
```

- **LGPD:** sinaliza CPF, telefone, e-mail e endereço com recomendação `mask`, `restrict` ou `review`.
- **Explicável:** cada resultado traz a evidência e se precisa de revisão humana.
- **Limites:** a calibração é provisória e os benchmarks são pequenos. Colunas de sim/não só pelo
  nome acertam cerca de 40%; com os valores, o acerto é alto. Veja
  [benchmarks/README.md](https://github.com/Caio-Analytics/colsemantics/blob/main/benchmarks/README.md).
- O código e a documentação técnica estão em inglês; issues e discussões em português são bem-vindos.

## License

MIT. Word lists derived from public sources are described in
[src/colsemantics/data/SOURCES.md](https://github.com/Caio-Analytics/colsemantics/blob/main/src/colsemantics/data/SOURCES.md).
