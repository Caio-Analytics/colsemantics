import pytest

from colsemantics.calibration import bucket_for, calibrate, requires_review


def test_calibration_uses_bucket_precision_and_review_threshold():
    assert bucket_for(0.83) == "0.8-0.9"
    assert calibrate(0.83, "pt-BR") == 0.88
    assert requires_review(0.79) is True
    assert requires_review(0.80) is False


@pytest.mark.parametrize(
    ("raw_confidence", "expected_bucket"),
    [(0.0, "0.0-0.1"), (0.1, "0.1-0.2"), (1.0, "0.9-1.0")],
)
def test_bucket_for_includes_lower_boundaries(raw_confidence: float, expected_bucket: str):
    assert bucket_for(raw_confidence) == expected_bucket


def test_calibration_uses_midpoint_for_unknown_profiles_and_empty_buckets():
    assert calibrate(0.45, "unknown") == 0.45
    assert calibrate(0.05, "pt-BR") == 0.05


@pytest.mark.parametrize("raw_confidence", [-0.01, 1.01])
def test_bucket_for_rejects_scores_outside_unit_interval(raw_confidence: float):
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        bucket_for(raw_confidence)
