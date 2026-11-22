# Benchmarks

| File | Purpose |
|---|---|
| `synthetic.json` | Small regression fixture. `calibration.json` was derived from it, so it must not be used to judge accuracy. |
| `validation.json` | Held-out validation set. Written separately from the calibration fixture and **never used to build `calibration.json` or tune vocabularies by case**. Mixes Brazilian and US column names, sampled values, and detected patterns. |
| `holdout-v2.json` | 37 cases written *before* the Brazilian/US pattern work, with column names not in `validation.json`. Scored 57% before that work and 92% after. Vocabulary additions were chosen by looking at `validation.json` failures and general English/Portuguese naming, so treat `holdout-v2.json` as a weaker check than a truly unseen set: some added terms (for example `notes`, `amount`) happen to overlap. |
| `public-us-socrata.json` | 390 columns from the test half of about 4,500 US open datasets (Socrata catalog), 130 each of date, geographic, and flag columns. Labels come from the dataset owner's declared column type (`Calendar date`, `Point`/`Polygon`/..., `Checkbox`), so they are weak and noisy, especially for flags. The vocabulary work only looked at the other half of the datasets, so this is the cleanest held-out check. |
| `public-br-es.json` | 51 Brazilian column names from `dados.es.gov.br`, labeled by hand. **Not clean**: the portal was held out while collecting vocabulary, but I then looked at its failures and added a few terms (for example `desclassificado`, `microregiao`, `numero`). Treat it as a regression test. |
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
| after public-catalog vocabulary (0.4.0) | 96% | 95% | see below |

Public samples, before and after the public-catalog vocabulary of 0.4.0:

| Set | Before | After |
|---|---|---|
| `public-us-socrata.json` (390, clean held-out) | 47.7% | 63.1% |
| `public-br-es.json` (51, partly tuned) | 76.5% | 100% |

On the full test half of the US datasets (1,522 unique column and label pairs, name-only inference) accuracy went from 64.5% to 77.2%. Dates are now mostly right (87%), geographic columns about 79%. Flags are still poor (18%): `Checkbox` columns have arbitrary names (`gun_related`, `in_stock`), so names alone rarely say they are flags.
