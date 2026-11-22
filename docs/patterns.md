# Value patterns and locales

When a column has sampled values, colsemantics looks at how they are written. Detection uses the
values only, so it works the same for Brazilian and US data and does not depend on the
vocabulary profile. A pattern is reported when at least 80% of the sampled values match (60% for
addresses).

| Type | Brazil (BR) | United States (US) |
|---|---|---|
| `phone` | `(11) 91234-5678`, `11 91234-5678`, `+55 11 91234-5678`, `(21) 3456-7890`, `0800 123 4567`. The area code (DDD) must exist; mobiles start with 9, landlines with 2 to 5. | `(415) 555-2671`, `415-555-2671`, `415.555.2671`, `+1 415 555 2671`. Area code and exchange start with 2 to 9 and are not N11. |
| `postal_code` | CEP `01310-100` | `94105-1234` (ZIP+4) |
| `address` | `Rua das Flores, 123`, `Av. Paulista, 1578`, `Rodovia BR-101 km 5` | `123 Main St`, `500 N. Michigan Ave., Suite 300`, `PO Box 1234` |
| national id | `cpf`, `cnpj` (check digits verified) | `ssn` (area, group, and serial ranges verified), `ein` (format only) |
| any | `email`, `uuid`, `geometry` (WKT), `coordinates` (`(lat, lon)`, address plus coordinates) | |

## What the result says

```python
from colsemantics import infer_column
from colsemantics.profiling import profile_values

result = infer_column("f6", profile=profile_values(["(11) 91234-5678", "(21) 99876-5432"]))
result["pattern"]
# {"type": "phone", "locale": "BR", "variant": "mobile", "format": "(DD) 9NNNN-NNNN",
#  "coverage": 1.0, "validated": True,
#  "message": "100% of sampled values look like a Brazilian mobile phone number (e.g. (DD) 9NNNN-NNNN)"}
```

`validated` is `True` only when a checksum or numbering-plan rule confirmed the values. Addresses
are heuristic and never validated. The same message becomes the `evidence` of the classification.

## Sensitivity

| Detected | `level` / `action` |
|---|---|
| Validated CPF or SSN | `high` / `mask` |
| Street address | `high` / `mask` |
| Person identity semantic | `high` / `restrict` |
| Contact semantic (e-mail, phone) | `high` / `mask` |
| CNPJ, EIN, postal code, coordinates, other identifiers | `medium` / `review` |
| Everything else | `none` / `allow` |

The recommendation is descriptive. colsemantics never changes your data.

## Limits

- Bare digit strings such as `4155552671`, `11912345678`, or a plain five-digit ZIP are not
  reported as phones or postal codes: they cannot be told apart from ids and amounts.
- Only Brazilian and US formats are recognized. Other countries are not detected.
- Address matching is heuristic. Expect misses on unusual formats and some false positives on text
  that starts with a number followed by a street word.
- Matching is exact (accent-insensitive) for reference lists such as municipalities and first
  names; misspelled values do not match.
