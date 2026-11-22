# Contributing to colsemantics

Thanks for helping. This guide covers setup, checks, and what a good pull request looks like.

## Development setup

```bash
git clone https://github.com/Caio-Analytics/colsemantics
cd colsemantics
python -m venv .venv && source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Python 3.10 or newer is required.

## Checks

CI runs all of these on Python 3.10 to 3.14, plus a job with the lowest supported dependency versions.

```bash
pytest
ruff check .
ruff format --check .   # `ruff format .` fixes it
mypy
```

## Pull requests

1. Open an issue first for new features or behavior changes, so the approach can be agreed before you invest time.
2. Branch from `main`, keep the change focused, and add tests. Bug fixes need a regression test.
3. Update `README.md` for user-visible changes and add a line to `CHANGELOG.md` under **Unreleased**.
4. Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `refactor:`).

## Vocabulary and calibration changes

Classification quality is data-driven. A change to vocabularies, detectors, or `calibration.json` should show its effect with the benchmark:

```bash
colsemantics benchmark benchmarks/synthetic.json --output benchmark-report.json
```

Include before and after accuracy and calibration error in the PR description. Use only synthetic or public data in fixtures. Never commit real customer data or personal information.

## Dependencies

Runtime dependencies keep a lower bound only (`rapidfuzz`, `unidecode`, `PyYAML`). Do not raise a bound unless the code needs it. If you do, say why in the PR. Dependabot proposes tool and action updates weekly.

## Releasing (maintainers)

1. Bump `version` in `pyproject.toml` and `__version__` in `src/colsemantics/__init__.py`.
2. Move the **Unreleased** changelog entries under the new version.
3. Merge to `main`, then publish a GitHub Release tagged `vX.Y.Z`. The tag must equal the package version or the workflow fails.
4. The `Publish to PyPI` workflow builds and uploads using PyPI trusted publishing. The `pypi` environment requires reviewer approval, so approve the deployment within 30 days or the run times out.

## Conduct

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). Report security issues as described in [SECURITY.md](SECURITY.md).
