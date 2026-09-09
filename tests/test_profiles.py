import pytest

from colsemantics import infer_column
from colsemantics.profiles import available_profiles, load_profile, temporary_profile


def test_loads_the_embedded_portuguese_profile():
    assert available_profiles() == ("pt-BR",)
    assert load_profile().strong_categories


def test_unknown_profile_lists_available_profiles():
    with pytest.raises(ValueError, match="pt-BR"):
        load_profile("en-US")


def test_yaml_extension_is_scoped_to_the_selected_profile(tmp_path):
    vocabulary = tmp_path / "company.yaml"
    vocabulary.write_text("column_overrides:\n  cost_bucket: Finance / Cost\n", encoding="utf-8")

    with temporary_profile("pt-BR", str(vocabulary)):
        assert infer_column("cost_bucket")["semantic"] == "Finance / Cost"

    assert infer_column("cost_bucket")["semantic"] != "Finance / Cost"
