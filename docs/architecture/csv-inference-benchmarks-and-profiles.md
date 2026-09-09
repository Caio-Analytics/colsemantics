# CSV Inference, Benchmarks, and Vocabulary Profiles

## Purpose

Add a practical file interface, measurable quality controls, and explicit vocabulary selection without coupling the core inference engine to a dataframe library or a specific business domain.

## Scope

The first iteration supports CSV input only. Parquet is deliberately out of scope until CSV behavior, reports, and benchmark metrics are stable.

## Command-line interface

The package exposes a `colsemantics` command with an `infer` subcommand:

```text
colsemantics infer input.csv --profile pt-BR --sample 10000 --output report.json
```

The command reads the CSV header and at most the requested number of data rows using the Python standard library. It builds a `ContentProfile` for each column and writes a report containing source metadata, selected profile, inferred columns, and summary counts. JSON is the initial output format. Invalid paths, invalid encodings, malformed CSV data, missing headers, and unknown profiles produce actionable non-zero errors.

The inference engine remains independent from filesystem and CLI concerns. A small application layer owns CSV sampling and report serialization.

## Vocabulary profiles

Profiles are named, immutable default contexts. The first embedded profile is `pt-BR`, preserving the current vocabulary behavior. The API accepts a profile name and optional external YAML paths; the latter extend the selected profile without mutating global state.

```python
infer_column("cd_dpto", profile_name="pt-BR")
load_profile("pt-BR", vocabulary_paths="company.yaml")
```

The profile registry is the single authority for profile names. Unknown profile names list the available choices. YAML continues to use the existing English schema and may add strong categories, fuzzy categories, gazetteers, and overrides.

## Benchmarks

Synthetic fixtures live in the repository and run in CI. Each case records a profile, column name, optional sampled values or detected pattern, and expected semantic, role, or domain. The benchmark runner reports:

- overall exact-match accuracy;
- semantic, role, and domain accuracy independently;
- coverage, meaning the share of cases not classified as `Generic / Unmapped`;
- per-profile metrics and a confusion matrix.

The public corpus is referenced by a manifest with source URL, license, checksum, and expected adapter. It is not bundled into the wheel or required by CI. A dedicated command downloads or receives its local path only when a maintainer deliberately runs the broader evaluation.

## Testing and compatibility

Tests cover deterministic CSV sampling, report shape, invalid CLI arguments, profile isolation, external vocabulary composition, synthetic benchmark metrics, and no regression to the current `infer_column` and `infer_table` contracts. The CLI uses only standard-library CSV support, so no pandas dependency is introduced.

## Release boundary

This is a feature release after the current standalone-English API. It does not publish automatically. A release candidate requires the complete test suite, linting, type checking, package build, wheel smoke test, and a benchmark baseline recorded in the changelog or release notes.
