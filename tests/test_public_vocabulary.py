import pytest

from colsemantics import infer_column, tokenize
from colsemantics._data import load_wordlist
from colsemantics.profiling import profile_values


@pytest.mark.parametrize(
    ("name", "tokens"),
    [
        ("issueddate", ["issued", "date"]),
        ("objectid", ["object", "id"]),
        ("expirationdate", ["expiration", "date"]),
        ("datecreated", ["date", "created"]),
        ("timecreate", ["time", "create"]),
        ("dataasof", ["data", "asof"]),
        ("lastupdated", ["last", "updated"]),
        ("createdon", ["created", "date"]),
        ("(zip)", ["zip"]),
        ("s/a", ["s", "a"]),
        ("CodigoPrograma", ["codigo", "programa"]),
    ],
)
def test_fused_and_punctuated_names_are_split(name, tokens):
    assert tokenize(name) == tokens


@pytest.mark.parametrize(
    "name", ["candidate", "mandate", "database", "valid", "paid", "update", "outside", "geocode"]
)
def test_ordinary_words_are_not_split(name):
    assert tokenize(name) == [name]


@pytest.mark.parametrize(
    ("name", "semantic"),
    [
        ("issueddate", "Date / Calendar"),
        ("expirationdate", "Date / Calendar"),
        ("year", "Date / Calendar"),
        ("fecha", "Date / Calendar"),
        ("the_geom", "Geographic Location"),
        ("geolocation", "Geographic Location"),
        ("georeference", "Geographic Location"),
        ("census_tract", "Geographic Location"),
        ("population", "Quantity / Metric"),
        ("NumeroLicitacao", "Identifier (ID)"),
        ("user_uuid", "Identifier (ID)"),
        ("DescricaoItemCompra", "Free-form Text"),
        ("ValorPago", "Financial Value"),
        ("website", "Contact / Network"),
        ("nombre", "Person Name / Identifier"),
    ],
)
def test_vocabulary_learned_from_public_catalogs(name, semantic):
    assert infer_column(name)["semantic"] == semantic


@pytest.mark.parametrize(
    ("name", "domain"),
    [
        ("property_type", "Real Estate / Property"),
        ("tarifa_energia", "Energy / Utilities"),
        ("violation_description", "Legal / Compliance"),
        ("covid_cases", "Health / Medical"),
    ],
)
def test_new_domains(name, domain):
    assert infer_column(name)["domain"] == domain


@pytest.mark.parametrize(
    ("values", "semantic", "evidence"),
    [
        (["Maria Silva", "José Santos", "Ana Souza", "Carlos Lima", "Paulo Rocha"], "Person Name / Identifier", "first name"),
        (["John Smith", "Mary Jones", "Robert Brown", "Linda Davis", "James Miller"], "Person Name / Identifier", "first name"),
        (["São Paulo", "Campinas", "Belo Horizonte", "Niterói", "Maringá"], "Geographic Location", "município"),
        (["Chicago", "Houston", "Phoenix", "Seattle", "Denver"], "Geographic Location", "US city"),
        (["Brasil", "Estados Unidos", "Argentina", "Portugal", "Japão"], "Geographic Location", "country"),
    ],
)  # fmt: skip
def test_gazetteers_classify_opaque_columns(values, semantic, evidence):
    result = infer_column("f1", profile=profile_values(values))

    assert result["semantic"] == semantic
    assert evidence in result["evidence"]


@pytest.mark.parametrize(
    "values",
    [
        ["Active", "Inactive", "Pending", "Closed", "Open", "Review"],
        ["red", "green", "blue", "yellow", "black", "white"],
        ["Widget", "Gadget", "Gizmo", "Doohickey", "Thingamajig", "Whatsit"],
        ["Maria"],
    ],
)
def test_gazetteers_do_not_fire_on_unrelated_values(values):
    assert infer_column("f1", profile=profile_values(values))["semantic"] == "Generic / Unmapped"


def test_wordlists_are_normalized_and_non_trivial():
    for name, minimum in (
        ("br_municipalities.txt", 5000),
        ("us_cities.txt", 2000),
        ("countries.txt", 200),
        ("br_first_names.txt", 300),
        ("us_first_names.txt", 1000),
        ("modifiers.txt", 500),
    ):
        words = load_wordlist(name)
        assert len(words) >= minimum, name
        assert all(word == word.lower() and word.isascii() for word in words), name
