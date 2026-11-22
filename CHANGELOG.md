# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.4.2]

Documentation, discoverability, and one bug fix. No API changes.

### Fixed
- A column named `state` whose values are US states (or any reference list) was classified as a flag because of the ambiguous name token. Sampled values that match a reference list now outweigh an ambiguous name.

### Added
- README rewritten: real sample output, use cases, comparison with neighboring tools, accuracy and limits, and a Portuguese section.
- `docs/` with an API reference, value patterns, and custom vocabularies; the planning documents moved to `docs/archive/plans/`.
- `examples/` with Brazilian and US sample CSVs and `quickstart.py`; tests keep the README demo and the API reference in sync with the code.
- Docstrings for every public function and class.
- `CITATION.cff`; PyPI keywords (LGPD, GDPR, PII detection, data catalog, ...), classifiers (English and Brazilian Portuguese, security topic), a Documentation link, and a clearer summary.

## [0.4.1]

### Added
- `colsemantics benchmark` reports `label_accuracy` (accuracy and case count per expected label).
- Value formats: ISO and US timestamps with time and zone, `Y/N`, `T/F`, and `S/N` booleans, WKT geometry (`geometry`), coordinate pairs and `address (lat, lon)` text (`coordinates`, medium/review sensitivity).
- Question-style names (`PPS Psych?`), more predicate words for flags (`allowed`, `required`, `needed`, `accessible`, `review`, `bool`), `...flag` suffix splitting, and compounds `total_price`, `unit_price`, `num_items`, `number_of`.
- `benchmarks/public-us-socrata.json` now carries real sample values; the names-only version is `public-us-socrata-names-only.json`. `scripts/fetch_public_values.py`.
- Test floors: every benchmark set must reach 60% overall and per label (labels with 10+ cases).

### Changed
- Benchmark values are profiled like CSV values (typed), not as plain text.
- Strong geometry or coordinate values now decide the domain over a weak name-derived role.
- The whole-name fuzzy comparison ignores words much shorter than the name (`customer_name` is no longer similar to `custo`).

### Fixed
- Checkbox columns judged with their values: 100% flags on both halves of the US sample (was 23% by name).
- Documented limit: Checkbox columns judged by name alone stay near 40%; the names carry no signal. See `benchmarks/README.md`.

## [0.4.0]

### Breaking
- Python 3.10 is no longer supported (end of life; `rapidfuzz>=3.14.6` needs 3.11).
- `infer_csv` samples uniformly at random (seeded) by default instead of taking the first rows; pass `sampling="head"` for the old behavior. The report gains `rows_read`, `rows_malformed`, `warnings`, `sampling`, and per-column `column_name`/`column_index`.
- Results gain a `pattern` key. `detected_pattern` names are English keys (`cpf`, `email`, `phone`, `postal_code`, ...); the legacy `CPF`, `E-mail`, `Telefone`, and `CEP` still work.
- `Free-form Text` is now a structural role, so `item_description` is classified as free text instead of `Product / Item`.
- `normalizar` and `tokenizar` are deprecated aliases of `normalize` and `tokenize` (removed in 1.0).

### Added
- Vocabulary learned from public open-data catalogs (about 4,500 US Socrata datasets and 500 Brazilian CKAN resources): roughly 190 new English, Portuguese, and Spanish terms, four new domains (`Real Estate / Property`, `Energy / Utilities`, `Legal / Compliance`, `Health / Medical`), and multi-word terms such as `phone_number` and `zip_code`.
- Fused column names are split when one part is a known modifier: `issueddate`, `objectid`, `datecreated`, `lastupdated`, `createdon`. Punctuation such as `(zip)` is a separator.
- Gazetteers from public sources for value-based inference: Brazilian municipalities (IBGE), US cities, countries, and common Brazilian (IBGE) and US (SSA) first names, plus a US state list. See `src/colsemantics/data/SOURCES.md` and `scripts/`.
- `benchmarks/public-us-socrata.json` (390 columns labeled by their dataset's declared type) and `benchmarks/public-br-es.json` (51 hand-labeled Brazilian columns).

### Added
- Locale-aware value patterns for Brazil and the US: phone (mobile, landline, toll-free, NANP), postal code (CEP, ZIP+4), street addresses (including PO boxes and highways), CPF, CNPJ, SSN, EIN. Results include `pattern` with `type`, `locale`, `variant`, `format`, `coverage`, `validated`, and a message.
- Sensitivity rules for SSN, addresses, EIN, and postal codes.
- English vocabulary (dates, flags, money, quantities, text, contact, address terms), multi-word terms such as `phone_number` and `zip_code`, and a US state gazetteer.
- `infer_csv`: delimiter detection and `--delimiter`, `utf-8-sig` default with clear decode errors, typed profiles (Boolean/Integer/Decimal/Date/Text), seeded reservoir sampling (`--sampling`, `--seed`), duplicate-header and malformed-row warnings, and `column_name`/`column_index` in the report.
- Typed results (`InferenceResult`, `CsvReport`, ...), strict mypy, `benchmarks/validation.json` and `benchmarks/holdout-v2.json`.

### Fixed
- Build backend floor: `setuptools>=68` could not build this project, because `license = "MIT"` (a PEP 639 license expression) needs setuptools 77 or newer. The floor is now `setuptools>=84.2.1`, the release suggested by Dependabot (published 2026-10-20, past the 14-day cooldown).
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
