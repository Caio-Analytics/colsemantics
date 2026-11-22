# Benchmarks

| File | Purpose |
|---|---|
| `synthetic.json` | Small regression fixture. `calibration.json` was derived from it, so it must not be used to judge accuracy. |
| `validation.json` | Held-out validation set. Written separately from the calibration fixture and **never used to build `calibration.json` or tune vocabularies by case**. Mixes Brazilian and US column names, sampled values, and detected patterns. |
| `holdout-v2.json` | 37 cases written *before* the Brazilian/US pattern work, with column names not in `validation.json`. Scored 57% before that work and 92% after. Vocabulary additions were chosen by looking at `validation.json` failures and general English/Portuguese naming, so treat `holdout-v2.json` as a weaker check than a truly unseen set: some added terms (for example `notes`, `amount`) happen to overlap. |
| `public-us-socrata.json` | 360 columns from the test half of about 4,500 US open datasets (Socrata catalog), 120 each of date, geographic, and flag columns, **with up to ten real sample values per column** (street lines redacted). This is how the package is normally used (CSV with values). Labels come from the dataset owner's declared column type (`Calendar date`, `Point`/`Polygon`/..., `Checkbox`). The vocabulary and rules were tuned only on the other half of the datasets. |
| `public-us-socrata-names-only.json` | 390 columns from the same test half, names only. Date and geographic columns are fine; Checkbox columns are not (see below). |
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

## 0.4.1: the 60% rule and the Checkbox problem

Every set must reach 60% overall, and every label with at least ten cases must reach 60% on its own (`tests/test_validation_corpus.py`). The report from `colsemantics benchmark` now includes `label_accuracy`, so a strong label cannot hide a weak one.

| Set | Overall | Worst label |
|---|---|---|
| `validation.json` | 98% | 67% (Generic, 3 cases) |
| `holdout-v2.json` | 100% | 100% |
| `public-br-es.json` | 100% | 100% |
| `public-us-socrata.json` (names + values) | 98% | 96% (geographic) |
| `public-us-socrata-names-only.json` | 69% | **40% (flags)** |

**Why flags by name alone stay below 60%.** A Checkbox column is a yes/no question and its name is arbitrary: `Domestic`, `Latino`, `Safety`, `Painted`, `in_stock`. No vocabulary can separate those from a text or category column. With the column values (`true/false`, `Y/N`, ...), flags are recognized 100% of the time. The names-only floor for flags is therefore a documented exception that only guards against regression (35%); everything else in that set clears 60%.

**Label noise.** I compared 60 random labels with the description the dataset owner wrote for each column and found no wrong label (0 of 60, so the error rate is below about 5% with 95% confidence). The labels are weak because they come from declared types, not because they are wrong. The real noise is in the source data: a few columns named `Speed` or `PM_Count` hold dates, and the engine follows the name.

**What changed in the engine.** Date and boolean formats with times and single letters (`2020-01-31T00:00:00.000`, `03/15/2021 02:30:00 PM`, `Y/N`, `T/F`), WKT geometry (`POINT (...)`, `POLYGON ...`), coordinate pairs including `address (lat, lon)` text, question-style names (`PPS Psych?`), predicate words (`allowed`, `required`, `needed`, `accessible`, `review`, `bool`), `...flag` suffixes, and compounds such as `total_price` and `num_items`. On the train half of the US datasets name+values accuracy is 99.0% and on the test half 98.7%; names alone went from 64.5% to 79.1% (test half).
