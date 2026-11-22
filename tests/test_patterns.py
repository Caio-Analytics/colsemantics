import pytest

from colsemantics.patterns import (
    analyze_values,
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


@pytest.mark.parametrize(
    ("value", "locale", "variant"),
    [
        ("(11) 91234-5678", "BR", "mobile"),
        ("11 91234-5678", "BR", "mobile"),
        ("+55 11 91234-5678", "BR", "mobile"),
        ("+5511912345678", "BR", "mobile"),
        ("(21) 3456-7890", "BR", "landline"),
        ("0800 123 4567", "BR", "toll-free"),
        ("(415) 555-2671", "US", None),
        ("415-555-2671", "US", None),
        ("415.555.2671", "US", None),
        ("+1 415 555 2671", "US", None),
        ("1-415-555-2671", "US", None),
        ("+14155552671", "US", None),
    ],
)
def test_phone_locale_and_variant(value, locale, variant):
    info = analyze_values([value])

    assert info is not None
    assert (info["type"], info["locale"], info["variant"]) == ("phone", locale, variant)
    assert info["validated"]


@pytest.mark.parametrize(
    "value",
    ["4155552671", "11912345678", "(00) 91234-5678", "(11) 81234-5678", "(115) 555-2671",
     "(415) 111-2671", "123-456", "call me"],
)  # fmt: skip
def test_non_phones_are_rejected(value):
    info = analyze_values([value])
    assert info is None or info["type"] != "phone"


def test_phone_message_names_the_locale_and_format():
    info = analyze_values(["(11) 91234-5678", "(21) 99876-5432", "(31) 98888-7777"])

    assert info is not None
    assert info["locale"] == "BR"
    assert info["format"] == "(DD) 9NNNN-NNNN"
    assert info["coverage"] == 1.0
    assert info["message"].startswith("100% of sampled values look like a Brazilian mobile phone")


def test_us_phone_column_is_reported_as_us():
    info = analyze_values(["(415) 555-2671", "(212) 555-0199", "(310) 555-0142"])

    assert info is not None
    assert info["message"].startswith("100% of sampled values look like a US phone number")


def test_mixed_locales_report_the_dominant_one():
    values = ["(415) 555-2671", "(212) 555-0199", "(310) 555-0142", "(11) 91234-5678"]

    info = analyze_values(values)

    assert info is not None
    assert (info["locale"], info["coverage"]) == ("US", 0.75 + 0.25)  # both are phones


@pytest.mark.parametrize(
    ("value", "locale", "variant"),
    [("01310-100", "BR", "CEP"), ("94105-1234", "US", "ZIP+4")],
)
def test_postal_codes(value, locale, variant):
    info = analyze_values([value])

    assert info is not None
    assert (info["type"], info["locale"], info["variant"]) == ("postal_code", locale, variant)


def test_ssn_and_ein():
    ssn = analyze_values(["123-45-6789", "078-05-1120"])
    assert ssn is not None and (ssn["type"], ssn["locale"], ssn["validated"]) == ("ssn", "US", True)
    assert analyze_values(["000-12-3456", "666-12-3456", "900-12-3456"]) is None
    ein = analyze_values(["12-3456789", "98-7654321"])
    assert ein is not None and (ein["type"], ein["validated"]) == ("ein", False)


@pytest.mark.parametrize(
    ("value", "locale"),
    [
        ("Rua das Flores, 123", "BR"),
        ("Av. Paulista, 1578 - Bela Vista", "BR"),
        ("Avenida Brasil 500", "BR"),
        ("R. XV de Novembro, s/n", "BR"),
        ("Praça da Sé, 100", "BR"),
        ("Rodovia BR-101 km 5", "BR"),
        ("123 Main St", "US"),
        ("742 Evergreen Terrace", "US"),
        ("1600 Pennsylvania Avenue NW, Washington, DC 20500", "US"),
        ("500 N. Michigan Ave., Suite 300", "US"),
        ("PO Box 1234", "US"),
        ("P.O. Box 77", "US"),
    ],
)
def test_street_addresses_by_locale(value, locale):
    info = analyze_values([value])

    assert info is not None
    assert (info["type"], info["locale"]) == ("address", locale)
    assert not info["validated"]


@pytest.mark.parametrize(
    "value", ["Main", "John Smith", "123", "Rua", "Springfield", "The quick brown fox jumps"]
)
def test_plain_text_is_not_an_address(value):
    info = analyze_values([value])
    assert info is None or info["type"] != "address"


def test_full_us_address_variant():
    info = analyze_values(["1600 Pennsylvania Avenue NW, Washington, DC 20500"])

    assert info is not None and info["variant"] == "full"
