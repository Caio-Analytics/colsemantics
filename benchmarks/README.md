# Benchmarks

| File | Purpose |
|---|---|
| `synthetic.json` | Small regression fixture. `calibration.json` was derived from it, so it must not be used to judge accuracy. |
| `validation.json` | Held-out validation set. Written separately from the calibration fixture and **never used to build `calibration.json` or tune vocabularies by case**. Mixes Brazilian and US column names, sampled values, and detected patterns. |
| `public-corpora.json` | Source manifests for public corpora. Not downloaded or bundled. |

`validation.json` is hand-written and synthetic. It measures regressions and gaps across Brazilian and US naming, but it is not a substitute for a large, independently labeled public corpus. Report its numbers as "accuracy on a 52-case synthetic validation set", not as production accuracy.

```bash
colsemantics benchmark benchmarks/validation.json --output validation-report.json
```

Labels reflect the reviewer's judgment; open an issue if you disagree with one.
