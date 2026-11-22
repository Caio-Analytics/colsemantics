# API reference

```python
from colsemantics import infer_column, infer_table, infer_csv
```

Every name below is exported from the top-level package. `help(colsemantics.<name>)` shows the
full docstring.

## Inference

### `infer_column(column_name, detected_pattern="None", profile=None) -> InferenceResult`

Classify one column from its name and, optionally, sampled values.

### `infer_table(columns) -> list[InferenceResult]`

Classify a whole table. `columns` is a list of dicts with `column_name` (or `name`) and
optionally `profile` and `detected_pattern`. Confident columns act as context for ambiguous ones.

### `infer_csv(path, *, sample_size=10000, profile_name="pt-BR", vocabulary_paths=None, encoding="utf-8-sig", delimiter=None, sampling="reservoir", seed=0) -> CsvReport`

Read a CSV, detect the delimiter, profile each column, and classify it. `sampling="reservoir"`
draws a uniform random sample of `sample_size` rows from the whole file; `"head"` takes the first
rows.

## Result shape

`InferenceResult` (a `TypedDict`):

| Key | Meaning |
|---|---|
| `semantic` | Final label, for example `Contact / Network` |
| `role` | Structural role (identifier, date, financial value, ...) or `None` |
| `domain` | Business domain (geographic, finance, ...) or `None` |
| `raw_confidence` | Score assembled from the evidence |
| `confidence` | Calibrated score (provisional calibration, see README) |
| `evidence` | Why this label was chosen |
| `conclusive` | The winner leads the runner-up by a clear margin |
| `review_required` | `True` when `confidence` is below 0.80 |
| `sensitivity` | `{"level", "action", "reason"}` |
| `pattern` | `PatternInfo` or `None`: `type`, `locale`, `variant`, `format`, `coverage`, `validated`, `message` |
| `hypotheses` | Up to four ranked alternatives |

`CsvReport` adds `source`, `profile`, `sampling`, `sample_size`, `rows_read`, `rows_sampled`,
`rows_malformed`, `warnings`, `columns` (each a result plus `column_name` and `column_index`),
and `summary`.

## Building profiles

`ContentProfile` holds sampled values and statistics. `colsemantics.profiling.profile_values(values)`
builds one from raw strings (type detection for Brazilian and US numbers and dates).
`colsemantics.patterns.analyze_values(values)` returns the value format on its own.

## Profiles and vocabularies

| Function | Purpose |
|---|---|
| `available_profiles()` | Embedded profile names |
| `load_profile(name, vocabulary_paths)` | Context for a profile plus YAML extensions |
| `temporary_profile(name, vocabulary_paths)` | Apply a profile inside a `with` block |
| `load_vocabularies(paths, base)` | Merge YAML vocabularies into a context |
| `temporary_vocabulary(paths)` | Apply YAML vocabularies inside a `with` block |
| `export_overrides_template(report, path)` | Write reviewed labels as `column_overrides` YAML |
| `current_context()` | The active `SemanticContext` |

## Confidence and sensitivity

| Function | Purpose |
|---|---|
| `calibrate(raw_confidence, profile_name)` | Map a raw score to the measured bucket precision |
| `requires_review(confidence)` | `True` below 0.80 |
| `assess_sensitivity(semantic, detected_pattern)` | `{"level", "action", "reason"}` |

## Text helpers

`normalize(text)` lowercases and strips accents. `tokenize(name)` splits `snake_case`,
`camelCase`, punctuation, and fused names such as `issueddate`. `normalizar` and `tokenizar` are
deprecated aliases that will be removed in 1.0.

## Types

`InferenceResult`, `CsvReport`, `CsvColumnResult`, `Hypothesis`, `PatternInfo`, `Sensitivity`,
`ContentProfile`, `SemanticContext`.

## Command line

```bash
colsemantics infer FILE.csv --output report.json [--profile pt-BR] [--sample 10000] \
    [--sampling reservoir|head] [--seed 0] [--delimiter ;] [--encoding utf-8-sig] \
    [--vocabulary extra.yaml]
colsemantics benchmark cases.json --output report.json
```

Exit code 0 on success, 2 on invalid input (the message goes to stderr).
