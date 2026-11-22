from colsemantics import ContentProfile, infer_column, infer_table
from colsemantics.csv_inference import infer_csv
from colsemantics.profiling import profile_values


def test_values_alone_reveal_a_brazilian_phone_column():
    profile = profile_values(["(11) 91234-5678", "(21) 99876-5432", "(31) 98888-7777"])

    result = infer_column("f6", profile=profile)

    assert result["semantic"] == "Contact / Network"
    assert result["pattern"] is not None
    assert (result["pattern"]["type"], result["pattern"]["locale"]) == ("phone", "BR")
    assert "Brazilian mobile phone" in result["evidence"]
    assert result["sensitivity"]["action"] == "mask"


def test_values_alone_reveal_a_us_phone_column():
    profile = profile_values(["(415) 555-2671", "(212) 555-0199", "(310) 555-0142"])

    result = infer_column("col_a", profile=profile)

    assert result["pattern"] is not None and result["pattern"]["locale"] == "US"
    assert result["semantic"] == "Contact / Network"


def test_postal_codes_are_geographic_and_reviewed():
    result = infer_column("col_b", profile=profile_values(["94105-1234", "10001-0001"]))

    assert result["semantic"] == "Geographic Location"
    assert result["sensitivity"] == {
        "level": "medium",
        "action": "review",
        "reason": "detected postal code pattern",
    }


def test_us_ssn_is_masked_and_not_confused_with_a_phone():
    result = infer_column("col_c", profile=profile_values(["123-45-6789", "234-56-7890"]))

    assert result["pattern"] is not None and result["pattern"]["type"] == "ssn"
    assert result["sensitivity"] == {
        "level": "high",
        "action": "mask",
        "reason": "validated SSN pattern",
    }


def test_street_addresses_are_geographic_and_masked():
    values = ["Rua das Flores, 123", "Av. Paulista, 1578", "Rua Augusta, 90", "Alameda Santos, 5"]

    result = infer_column("col_d", profile=profile_values(values))

    assert result["semantic"] == "Geographic Location"
    assert result["pattern"] is not None
    assert (result["pattern"]["type"], result["pattern"]["locale"]) == ("address", "BR")
    assert result["sensitivity"]["action"] == "mask"


def test_no_pattern_means_none():
    result = infer_column("employee_id")

    assert result["pattern"] is None


def test_reported_pattern_without_values_is_kept_without_a_locale():
    result = infer_column("field_1", detected_pattern="Telefone")

    assert result["pattern"] is not None
    assert (result["pattern"]["type"], result["pattern"]["locale"]) == ("phone", None)
    assert result["pattern"]["coverage"] is None


def test_reported_pattern_is_refined_by_the_values():
    profile = ContentProfile(distinct_values=["(415) 555-2671"], distinct_count=1)

    result = infer_column("field_1", detected_pattern="phone", profile=profile)

    assert result["pattern"] is not None and result["pattern"]["locale"] == "US"


def test_infer_table_reports_pattern_per_column():
    results = infer_table(
        [
            {"column_name": "a", "profile": profile_values(["(11) 91234-5678"])},
            {"column_name": "employee_id"},
        ]
    )

    assert results[0]["pattern"] is not None and results[0]["pattern"]["locale"] == "BR"
    assert results[1]["pattern"] is None


def test_csv_report_includes_locale_aware_patterns(tmp_path):
    source = tmp_path / "contacts.csv"
    source.write_text(
        "who,phone,zip\nAna,(11) 91234-5678,01310-100\nBob,(415) 555-2671,94105-1234\n",
        encoding="utf-8",
    )

    columns = {c["column_name"]: c for c in infer_csv(source)["columns"]}

    assert columns["phone"]["pattern"] is not None
    assert columns["phone"]["pattern"]["type"] == "phone"
    assert columns["zip"]["pattern"] is not None
    assert columns["zip"]["pattern"]["type"] == "postal_code"
