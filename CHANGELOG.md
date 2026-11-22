# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Locale-aware value patterns for Brazil and the US: phone (mobile, landline, toll-free, NANP), postal code (CEP, ZIP+4), street addresses (including PO boxes and highways), CPF, CNPJ, SSN, EIN. Results include `pattern` with `type`, `locale`, `variant`, `format`, `coverage`, `validated`, and a message.
- Sensitivity rules for SSN, addresses, EIN, and postal codes.
- English vocabulary (dates, flags, money, quantities, text, contact, address terms), multi-word terms such as `phone_number` and `zip_code`, and a US state gazetteer.
- `infer_csv`: delimiter detection and `--delimiter`, `utf-8-sig` default with clear decode errors, typed profiles (Boolean/Integer/Decimal/Date/Text), seeded reservoir sampling (`--sampling`, `--seed`), duplicate-header and malformed-row warnings, and `column_name`/`column_index` in the report.
- Typed results (`InferenceResult`, `CsvReport`, ...), strict mypy, `benchmarks/validation.json` and `benchmarks/holdout-v2.json`.

### Fixed
- Value patterns (CPF, e-mail, ...) were never detected in CSV input.
- `infer_table` no longer invents a column named `None` when `column_name` is missing; it raises `ValueError`.
- Legacy Portuguese `data_type` names were the only ones the structural rules understood; English names now work and the Portuguese ones are still accepted.
- A strong content domain (for example addresses) now beats a weak structural role guessed from an uninformative column name.

## [0.3.1]

### Added
- CI workflow: lint, format check, mypy, tests on Python 3.11 to 3.14, lowest-dependency job, and distribution check.
- Dependabot configuration, contribution guide, security policy, code of conduct, and pull request template.
- Release workflow verifies that the release tag matches the package version.

### Changed
- Raised dependency floors to releases at least 14 days old: `rapidfuzz>=3.14.6`, `unidecode>=1.4.0`, `PyYAML>=6.0.3` (6.0 has no Python 3.12 wheels). Dev tools: `pytest>=9.2.0`, `pytest-cov>=7.1.0`, `mypy>=2.4.1`, `ruff>=0.17.4`.
- Dependabot only proposes versions published at least 14 days ago (`cooldown`).
- Renamed `normalizar` to `normalize` and `tokenizar` to `tokenize`; the old names are deprecated aliases until 1.0.
- `__all__` now lists every public function, including `infer_table`, `assess_sensitivity`, `calibrate`, and `requires_review`.
- Test coverage is measured in CI with a minimum of 85%.
- Declared Python 3.13 and 3.14 support.
- Applied `ruff format` to the codebase.

### Removed
- Python 3.10 support. It is end of life and `rapidfuzz>=3.14.6` requires Python 3.11.

## [0.3.0]

Calibrated confidence (`raw_confidence`, `confidence`, `review_required`) and sensitive-data recommendations. Never tagged or published; its changes ship in 0.3.1.

## [0.2.0]

Scoped vocabularies and English package documentation. The GitHub release exists, but the PyPI upload never ran because the deployment approval timed out.

## [0.1.0]

Initial release.
