# Benchmarks

| File | Purpose |
|---|---|
| `synthetic.json` | Small regression fixture. `calibration.json` was derived from it, so it must not be used to judge accuracy. |
| `validation.json` | Held-out validation set. Written separately from the calibration fixture and **never used to build `calibration.json` or tune vocabularies by case**. Mixes Brazilian and US column names, sampled values, and detected patterns. |
| `holdout-v2.json` | 37 cases written *before* the Brazilian/US pattern work, with column names not in `validation.json`. Scored 57% before that work and 92% after. Vocabulary additions were chosen by looking at `validation.json` failures and general English/Portuguese naming, so treat `holdout-v2.json` as a weaker check than a truly unseen set: some added terms (for example `notes`, `amount`) happen to overlap. |
| `public-corpora.json` | Source manifests for public corpora. Not downloaded or bundled. |

`validation.json` is hand-written and synthetic. It measures regressions and gaps across Brazilian and US naming, but it is not a substitute for a large, independently labeled public corpus. Report its numbers as "accuracy on a small hand-written synthetic set", not as production accuracy.

```bash
colsemantics benchmark benchmarks/validation.json --output validation-report.json
```

Labels reflect the reviewer's judgment; open an issue if you disagree with one.

## History

| Date | `validation.json` | `holdout-v2.json` | Change |
|---|---|---|---|
| first measurement | 71% (52 cases) | 57% (37 cases) | before US/BR patterns and English vocabulary |
| after locale-aware patterns | 92% | 92% | `validation.json` failures informed the new vocabulary, so its gain is optimistic |
