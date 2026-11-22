# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- CI workflow: lint, format check, mypy, tests on Python 3.10 to 3.14, lowest-dependency job, and distribution check.
- Dependabot configuration, contribution guide, security policy, code of conduct, and pull request template.
- Release workflow verifies that the release tag matches the package version.

### Changed
- Raised the `PyYAML` lower bound to `6.0.1`. Version 6.0 has no wheels for Python 3.12 and fails to build from source.
- Declared Python 3.13 and 3.14 support.
- Applied `ruff format` to the codebase.

## [0.3.0]

Calibrated confidence (`raw_confidence`, `confidence`, `review_required`) and sensitive-data recommendations. Tagged in `pyproject.toml` but not yet released or published to PyPI.

## [0.2.0]

Scoped vocabularies and English package documentation. The GitHub release exists, but the PyPI upload never ran because the deployment approval timed out.

## [0.1.0]

Initial release.
