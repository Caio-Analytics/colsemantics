from colsemantics import infer_column
from colsemantics.sensitivity import assess_sensitivity


def test_validated_cpf_has_priority_over_generic_identifier():
    result = infer_column("field_1", detected_pattern="CPF")

    assert result["sensitivity"] == {
        "level": "high",
        "action": "mask",
        "reason": "validated CPF pattern",
    }


def test_sensitive_data_policy_covers_each_documented_rule():
    assert assess_sensitivity("Person Name / Identifier", "None") == {
        "level": "high",
        "action": "restrict",
        "reason": "person identity semantic",
    }
    assert assess_sensitivity("Contact / Network", "None") == {
        "level": "high",
        "action": "mask",
        "reason": "contact semantic",
    }
    assert assess_sensitivity("Identifier (ID)", "None") == {
        "level": "medium",
        "action": "review",
        "reason": "identifier semantic requires context",
    }
    assert assess_sensitivity("Financial Value", "None") == {
        "level": "none",
        "action": "allow",
        "reason": "no sensitive-data rule matched",
    }


def test_low_confidence_non_sensitive_result_can_still_require_review():
    result = infer_column("f27")

    assert result["sensitivity"]["level"] == "none"
    assert result["review_required"] is True
