from colsemantics.evidence import Evidence


def test_evidence_uses_english_fields():
    evidence = Evidence("Identifier (ID)", "role", 0.9, "exact token 'id'")

    assert evidence.category == "Identifier (ID)"
    assert evidence.axis == "role"
    assert evidence.weight == 0.9
    assert evidence.source == "exact token 'id'"
