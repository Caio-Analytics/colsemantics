import pytest

import colsemantics
from colsemantics import ContentProfile, infer_column, infer_table, load_vocabularies, tokenizar
from colsemantics.context import reset_context, set_context
from colsemantics.tokens import expand_abbreviation


def profile(values: list[str], data_type: str = "Text") -> ContentProfile:
    distinct_values = sorted(set(values))
    return ContentProfile(
        data_type=data_type,
        distinct_values=distinct_values,
        distinct_count=len(distinct_values),
        uniqueness_ratio=len(distinct_values) / len(values),
    )


def test_public_api_exposes_only_english_contract():
    assert colsemantics.__all__ == [
        "ContentProfile",
        "SemanticContext",
        "available_profiles",
        "current_context",
        "infer_csv",
        "infer_column",
        "infer_table",
        "load_profile",
        "normalizar",
        "load_vocabularies",
        "temporary_vocabulary",
        "temporary_profile",
        "export_overrides_template",
        "tokenizar",
    ]


def test_identifier_uses_english_taxonomy():
    result = infer_column("employee_id")
    assert result["semantic"] == "Identifier (ID)"
    assert result["role"] == "Identifier (ID)"


def test_result_has_only_english_keys():
    assert set(infer_column("department_name")) == {
        "semantic",
        "role",
        "domain",
        "raw_confidence",
        "confidence",
        "evidence",
        "conclusive",
        "review_required",
        "sensitivity",
        "hypotheses",
    }


@pytest.mark.parametrize(
    ("column_name", "semantic"),
    [
        ("id_funcionario", "Identifier (ID)"),
        ("dt_admissao", "Date / Calendar"),
        ("salary_amount", "Financial Value"),
        ("email", "Contact / Network"),
        ("xyzabc123", "Generic / Unmapped"),
    ],
)
def test_name_based_inference(column_name: str, semantic: str):
    assert infer_column(column_name)["semantic"] == semantic


def test_content_pattern_overrides_an_opaque_name():
    result = infer_column("field_1", detected_pattern="CPF")
    assert result["semantic"] == "Identifier (ID)"
    assert result["confidence"] >= 0.95


@pytest.mark.parametrize(
    ("values", "semantic"),
    [
        (["SP", "RJ", "MG", "BA"] * 10, "Geographic Location"),
        (["S", "N"] * 20, "Status / Indicator / Flag"),
        (["janeiro", "fevereiro", "marco"] * 10, "Date / Calendar"),
    ],
)
def test_values_resolve_an_opaque_name(values: list[str], semantic: str):
    assert infer_column("f27", profile=profile(values))["semantic"] == semantic


def test_independent_evidence_increases_confidence():
    values = ["SP", "RJ", "MG", "BA"] * 10
    from_name = infer_column("uf")
    from_values = infer_column("f27", profile=profile(values))
    combined = infer_column("uf", profile=profile(values))
    assert combined["raw_confidence"] > from_name["raw_confidence"]
    assert combined["raw_confidence"] > from_values["raw_confidence"]


def test_table_context_resolves_an_ambiguous_abbreviation():
    results = infer_table(
        [
            {"column_name": "matricula"},
            {"column_name": "nome_func"},
            {"column_name": "cod_dep"},
            {"column_name": "diretoria"},
            {"column_name": "dt_admissao"},
        ]
    )
    assert results[2]["domain"] == "Organizational Structure"


def test_table_api_accepts_english_input_keys():
    assert (
        infer_table([{"column_name": "department_name"}])[0]["domain"] == "Organizational Structure"
    )


def test_tokenization_handles_camel_and_snake_case():
    assert tokenizar("dt_admissao") == ["dt", "admissao"]
    assert tokenizar("hireDate") == ["hire", "date"]


def test_abbreviation_expansion_supports_portuguese_source_tokens():
    assert "departamento" in [word for word, _ in expand_abbreviation("dpto")]
    assert expand_abbreviation("name") == ()


def test_custom_vocabulary_is_scoped(tmp_path):
    vocabulary = tmp_path / "vocabulary.yaml"
    vocabulary.write_text("column_overrides:\n  cost_bucket: Finance / Cost\n", encoding="utf-8")
    token = set_context(load_vocabularies(str(vocabulary)))
    try:
        assert infer_column("cost_bucket")["semantic"] == "Finance / Cost"
    finally:
        reset_context(token)
    assert infer_column("cost_bucket")["semantic"] != "Finance / Cost"


def test_custom_gazetteer_rejects_an_invalid_axis(tmp_path):
    path = tmp_path / "vocabulary.yaml"
    path.write_text(
        "gazetteers:\n  - name: status\n    values: [open]\n    category: Status / Indicator / Flag\n    axis: category\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="axis"):
        load_vocabularies(str(path))


def test_custom_gazetteer_uses_english_schema(tmp_path):
    path = tmp_path / "vocabulary.yaml"
    path.write_text(
        "gazetteers:\n  - name: deployment status\n    values: [open, closed]\n    category: Status / Indicator / Flag\n    axis: role\n",
        encoding="utf-8",
    )
    token = set_context(load_vocabularies(str(path)))
    try:
        actual = infer_column("state", profile=profile(["open", "closed"] * 4))
        assert actual["role"] == "Status / Indicator / Flag"
    finally:
        reset_context(token)


def test_runtime_version_matches_the_release_candidate():
    assert colsemantics.__version__ == "0.3.0"


def test_public_api_exports_csv_and_profile_interfaces():
    assert {"available_profiles", "infer_csv", "load_profile", "temporary_profile"} <= set(
        colsemantics.__all__
    )


@pytest.mark.parametrize(
    ("column_name", "expected_semantic", "expected_role", "expected_domain"),
    [
        ("employee_id", "Identifier (ID)", "Identifier (ID)", None),
        ("start_date", "Date / Calendar", "Date / Calendar", None),
        (
            "department_name",
            "Organizational Structure",
            "Entity Label / Name",
            "Organizational Structure",
        ),
        ("xyzabc123", "Generic / Unmapped", None, None),
    ],
)
def test_english_core_regression_cases(
    column_name, expected_semantic, expected_role, expected_domain
):
    result = infer_column(column_name)
    assert result["semantic"] == expected_semantic
    assert result["role"] == expected_role
    assert result["domain"] == expected_domain


def test_english_core_regression_uses_profiled_values():
    profile = ContentProfile(
        data_type="Text",
        distinct_values=["SP", "RJ", "MG", "BA"],
        distinct_count=4,
        uniqueness_ratio=0.1,
    )
    assert infer_column("f27", profile=profile)["semantic"] == "Geographic Location"
