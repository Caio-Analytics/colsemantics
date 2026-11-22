import pytest

from colsemantics import infer_column
from colsemantics.profiling import detect_data_type, parse_number, profile_values


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["1", "2", "30"], "Integer"),
        (["1.5", "2,25"], "Decimal"),
        (["1.234,56", "10,00"], "Decimal"),
        (["1,234.56", "10.00"], "Decimal"),
        (["2024-01-31", "2024-02-01"], "Date"),
        (["31/01/2024", "01/02/2024"], "Date"),
        (["01/31/2024", "12/25/2024"], "Date"),
        (["true", "False", "yes"], "Boolean"),
        (["sim", "não"], "Boolean"),
        (["00123", "00456"], "Text"),
        (["SP", "RJ"], "Text"),
        (["2024-13-45"], "Text"),
        ([], "Text"),
    ],
)
def test_detect_data_type(values, expected):
    assert detect_data_type(values) == expected


@pytest.mark.parametrize(
    ("text", "number"),
    [("12", 12.0), ("-3,5", -3.5), ("1.234,5", 1234.5), ("1,234.5", 1234.5), ("abc", None)],
)
def test_parse_number(text, number):
    assert parse_number(text) == number


def test_profile_fills_numeric_statistics():
    profile = profile_values(["10.00", "20.00", "30.00", "400.00"])

    assert profile.data_type == "Decimal"
    assert profile.minimum == 10.0
    assert profile.fixed_decimal_places == 2
    assert profile.monotonically_increasing
    assert profile.skewness is not None and profile.skewness > 0.5


def test_unique_increasing_integers_look_like_identifiers():
    profile = profile_values([str(number) for number in range(1, 40)])

    assert profile.monotonically_increasing
    assert infer_column("f1", profile=profile)["semantic"] == "Identifier (ID)"


def test_date_formatted_values_look_like_dates():
    profile = profile_values(["2024-01-01", "2024-03-15", "2024-07-09"])

    assert infer_column("f2", profile=profile)["semantic"] == "Date / Calendar"


def test_legacy_portuguese_data_type_names_still_work():
    from colsemantics import ContentProfile

    profile = ContentProfile(
        data_type="Número Inteiro",
        distinct_count=50,
        uniqueness_ratio=1.0,
        monotonically_increasing=True,
    )
    assert infer_column("f3", profile=profile)["semantic"] == "Identifier (ID)"
