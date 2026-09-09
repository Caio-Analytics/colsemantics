# Confidence Calibration, Sensitive Data Policy, and English Core

## Purpose

Make confidence values empirically interpretable, expose a conservative sensitive-data policy, and complete the internal English migration without changing the intended classification behavior.

## Internal English migration

The classifier core uses English names for constants, axes, dataclasses, mapping keys, functions, variables, errors, and evidence messages. The current Portuguese vocabulary remains only as data inside the `pt-BR` profile: tokens, abbreviations, gazetteer values, and profile display metadata. Public results and configuration remain English-only.

The refactor must preserve detector ordering and weights. Existing behavior is protected by translated regression fixtures before identifiers are renamed.

## Confidence calibration

The engine keeps its existing noisy-OR result as `raw_confidence`. A versioned calibration table maps `(profile, raw-score bucket)` to empirical precision measured on held-out benchmark cases. The public `confidence` field becomes that calibrated value.

Calibration buckets use lower-inclusive 0.10 intervals from `0.0` through `1.0`; an unseen bucket falls back to its raw-score midpoint and reports no stronger claim than the input evidence. The calibration report records bucket count, correct count, empirical precision, and expected calibration error. Calibration data is regenerated explicitly from benchmark fixtures, never updated during inference.

Every inference result adds:

```python
{
    "raw_confidence": float,
    "confidence": float,
    "review_required": bool,
}
```

`review_required` is `True` when calibrated confidence is below `0.80`. It signals classifier uncertainty and is independent of data sensitivity.

## Sensitive data policy

Each inference result adds a `sensitivity` object:

```python
{
    "level": "none" | "medium" | "high",
    "action": "allow" | "review" | "mask" | "restrict",
    "reason": str,
}
```

Rules are evaluated in order:

1. A validated `CPF` content pattern is `high` / `mask` with reason `validated CPF pattern`.
2. `Person Name / Identifier` is `high` / `restrict` with reason `person identity semantic`.
3. `Contact / Network` is `high` / `mask` with reason `contact semantic`.
4. `Identifier (ID)` without a CPF pattern is `medium` / `review` with reason `identifier semantic requires context`.
5. All other semantics are `none` / `allow` with reason `no sensitive-data rule matched`.

The policy is deterministic and descriptive. It recommends handling; it does not transform source data.

## Benchmark changes

Benchmark fixtures declare expected semantic labels and may declare expected roles or domains as they do today. Benchmark evaluation additionally records each result's raw score, calibrated score, review decision, and calibration bucket. It reports calibration details by profile alongside existing accuracy, coverage, and confusion metrics.

The synthetic fixture remains a regression suite. Calibration is considered provisional until a held-out public corpus is curated, tracked with a manifest source and checksum, and added to the evaluation command.

## Testing and release boundary

Tests cover profile-specific calibration, empty buckets, review threshold behavior, every sensitive-data rule, policy precedence, and translated internal regression cases. The complete suite, linting, typing, package build, wheel smoke test, and benchmark report must pass before a release candidate is proposed.
