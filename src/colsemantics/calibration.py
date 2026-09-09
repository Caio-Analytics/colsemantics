import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_BUCKET_WIDTH = 0.1
_REVIEW_THRESHOLD = 0.80
_CALIBRATION_PATH = Path(__file__).with_name("calibration.json")


def bucket_for(raw_confidence: float) -> str:
    if not 0.0 <= raw_confidence <= 1.0:
        raise ValueError("raw_confidence must be between 0.0 and 1.0")
    lower_bound = min(int(raw_confidence / _BUCKET_WIDTH), 9) * _BUCKET_WIDTH
    upper_bound = lower_bound + _BUCKET_WIDTH
    return f"{lower_bound:.1f}-{upper_bound:.1f}"


def _bucket_midpoint(bucket: str) -> float:
    lower, upper = (float(bound) for bound in bucket.split("-", maxsplit=1))
    return round((lower + upper) / 2, 4)


@lru_cache(maxsize=1)
def load_calibration() -> dict[str, Any]:
    return json.loads(_CALIBRATION_PATH.read_text(encoding="utf-8"))


def calibrate(raw_confidence: float, profile_name: str) -> float:
    bucket = bucket_for(raw_confidence)
    profiles = load_calibration().get("profiles", {})
    profile = profiles.get(profile_name, {})
    precision = profile.get(bucket, {}).get("precision")
    if precision is None:
        return round(raw_confidence if profile_name not in profiles else _bucket_midpoint(bucket), 4)
    return round(float(precision), 4)


def requires_review(confidence: float) -> bool:
    return confidence < _REVIEW_THRESHOLD
