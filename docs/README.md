# Documentation

| Page | What it covers |
|---|---|
| [API reference](api.md) | Functions, result shape, CLI |
| [Value patterns](patterns.md) | Phone, postal code, address, ID, geometry formats for Brazil and the US |
| [Custom vocabularies](vocabulary.md) | YAML schema, gazetteers, overrides, data sources |
| [Benchmarks](../benchmarks/README.md) | Accuracy sets, what they measure, and their limits |
| [Architecture](architecture/) | Design notes for calibration, sensitivity, and CSV inference |
| [Changelog](../CHANGELOG.md) | Release notes and breaking changes |
| [Contributing](../CONTRIBUTING.md) | Setup, checks, releases |

`archive/plans/` keeps the implementation plans written while building 0.2 and 0.3. They are
historical and may not match the code.

`assets/social-preview.png` (1280x640) is the GitHub social preview image; `assets/social-preview.html`
is its source. To regenerate it:
`chromium --headless --window-size=1280,640 --screenshot=docs/assets/social-preview.png file://$PWD/docs/assets/social-preview.html`.
