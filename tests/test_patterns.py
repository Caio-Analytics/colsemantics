import pytest

from colsemantics.patterns import (
    canonical_pattern,
    detect_column_pattern,
    is_valid_cnpj,
    is_valid_cpf,
)


@pytest.mark.parametrize("value", ["529.982.247-25", "52998224725", "111.444.777-35"])
def test_valid_cpf(value):
    assert is_valid_cpf(value)


@pytest.mark.parametrize("value", ["529.982.247-26", "111.111.111-11", "123", "abc"])
def test_invalid_cpf(value):
    assert not is_valid_cpf(value)


def test_cnpj_check_digits():
    assert is_valid_cnpj("11.222.333/0001-81")
    assert not is_valid_cnpj("11.222.333/0001-82")
    assert not is_valid_cnpj("00000000000000")


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["529.982.247-25", "111.444.777-35"], "cpf"),
        (["11.222.333/0001-81"], "cnpj"),
        (["a@b.com", "x.y@z.org"], "email"),
        (["(11) 91234-5678", "+55 21 3456-7890"], "phone"),
        (["01310-100", "20040-020"], "postal_code"),
        (["123e4567-e89b-42d3-a456-426614174000"], "uuid"),
        (["12345678", "87654321"], "None"),
        (["Ana", "Bruno"], "None"),
        ([], "None"),
    ],
)
def test_detects_column_pattern(values, expected):
    assert detect_column_pattern(values) == expected


def test_requires_coverage_before_naming_a_pattern():
    values = ["a@b.com"] * 7 + ["not an email"] * 3
    assert detect_column_pattern(values) == "None"
    assert detect_column_pattern(values, minimum_coverage=0.7) == "email"


@pytest.mark.parametrize(
    ("legacy", "canonical"),
    [
        ("CPF", "cpf"),
        ("E-mail", "email"),
        ("Telefone", "phone"),
        ("CEP", "postal_code"),
        ("None", "None"),
        ("custom", "custom"),
    ],
)
def test_legacy_pattern_names_map_to_english_keys(legacy, canonical):
    assert canonical_pattern(legacy) == canonical
