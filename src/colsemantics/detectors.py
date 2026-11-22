from dataclasses import dataclass, field
from typing import Any

from rapidfuzz.distance import JaroWinkler

from . import _taxonomy as config
from .context import current_context
from .evidence import DOMAIN_AXIS, ROLE_AXIS, Evidence
from .results import PatternInfo
from .tokens import expand_abbreviation, expanded_tokens, normalize

STRUCTURAL_ROLES = frozenset(
    {
        config.IDENTIFIER_SEMANTIC,
        config.DATE_CALENDAR_SEMANTIC,
        "Financial Value",
        "Quantity / Metric",
        "Contact / Network",
        "Status / Indicator / Flag",
        "Assessment Result",
        config.FREE_FORM_TEXT_SEMANTIC,
    }
)

_PATTERN_SEMANTICS: dict[str, tuple[str, str]] = {
    "cpf": (config.IDENTIFIER_SEMANTIC, ROLE_AXIS),
    "cnpj": (config.IDENTIFIER_SEMANTIC, ROLE_AXIS),
    "ssn": (config.IDENTIFIER_SEMANTIC, ROLE_AXIS),
    "ein": (config.IDENTIFIER_SEMANTIC, ROLE_AXIS),
    "uuid": (config.IDENTIFIER_SEMANTIC, ROLE_AXIS),
    "email": ("Contact / Network", ROLE_AXIS),
    "phone": ("Contact / Network", ROLE_AXIS),
    "postal_code": ("Geographic Location", DOMAIN_AXIS),
    "address": ("Geographic Location", DOMAIN_AXIS),
}

_POSITIONAL_DECAY = 0.03


_MINIMUM_PREFIX_COVERAGE = 0.7
_MIN_DISTINCT_FOR_IDENTIFIER = 20  # tiny samples are trivially "unique"


@dataclass
class ContentProfile:
    data_type: str = ""
    distinct_values: list[str] = field(default_factory=list)
    distinct_count: int = 0
    uniqueness_ratio: float = 0.0
    mean_string_length: float | None = None
    fixed_length: bool = False
    skewness: float | None = None
    minimum: float | None = None
    monotonically_increasing: bool = False
    fixed_decimal_places: int | None = None


_DATA_TYPE_ALIASES = {
    "booleano": "Boolean",
    "número inteiro": "Integer",
    "numero inteiro": "Integer",
    "número decimal": "Decimal",
    "numero decimal": "Decimal",
    "data": "Date",
}


def normalize_data_type(data_type: str) -> str:
    """Map legacy Portuguese type names (``Número Inteiro``, ``Texto...``) to English."""
    key = data_type.strip().lower()
    if key.startswith("texto"):
        return "Text"
    return _DATA_TYPE_ALIASES.get(key, data_type)


def _positional_weight(index: int) -> float:
    return max(1.0 - _POSITIONAL_DECAY * index, 0.5)


def by_content_pattern(pattern: PatternInfo | None) -> list[Evidence]:
    """Evidence from a value format. Validated formats weigh more than heuristic ones."""
    if pattern is None:
        return []
    entry = _PATTERN_SEMANTICS.get(pattern["type"])
    if entry is None:
        return []
    category, axis = entry
    coverage = pattern["coverage"] if pattern["coverage"] is not None else 1.0
    weight = (0.98 if pattern["validated"] else 0.88) * (0.9 + 0.1 * coverage)
    return [Evidence(category, axis, round(weight, 4), pattern["message"])]


def by_gazetteer(profile: ContentProfile) -> list[Evidence]:
    if not profile.distinct_values or profile.distinct_count <= 0:
        return []

    normalized_values = [normalize(value) for value in profile.distinct_values]
    normalized_values = [value for value in normalized_values if value]
    if not normalized_values:
        return []

    findings: list[Evidence] = []
    first_tokens = [value.split()[0] for value in normalized_values]
    for gazetteer in current_context().gazetteers:
        if (
            not gazetteer.get("minimum_distinct", 1)
            <= profile.distinct_count
            <= gazetteer["max_distinct"]
        ):
            continue
        candidates = first_tokens if gazetteer.get("match") == "first_token" else normalized_values
        matches = sum(1 for value in candidates if value in gazetteer["values"])
        coverage = matches / len(candidates)
        if coverage < gazetteer["minimum_coverage"]:
            continue
        findings.append(
            Evidence(
                gazetteer["category"],
                gazetteer["axis"],
                round(gazetteer["weight"] * coverage, 4),
                f"values match {gazetteer['name']} ({coverage:.0%} of the column)",
            )
        )
    return findings


def _edge_qualifier(token: str, position: str) -> Evidence | None:
    candidates: list[tuple[str, float]] = [(token, 1.0)]
    expansions = expand_abbreviation(token)
    qualifiers = [entry for entry in expansions if entry[0] in config.QUALIFIER_TOKENS]
    if len(expansions) == 1:
        candidates.append(expansions[0])
    elif len(qualifiers) == 1:
        candidates.append(qualifiers[0])

    for word, confidence in candidates:
        if word not in config.QUALIFIER_TOKENS:
            continue
        categories = current_context().strong_token_index.get(word, ())
        if len(categories) != 1:
            continue
        source = (
            f"{position} qualifier '{word}'"
            if word == token
            else f"{position} qualifier '{token}' → '{word}'"
        )
        return Evidence(categories[0], ROLE_AXIS, round(0.9 * confidence, 4), source)
    return None


def _compound_evidence(tokens: list[str]) -> tuple[list[Evidence], set[int]]:
    """Match multi-word terms such as ``phone number``; return evidence and covered positions."""
    evidence_items: list[Evidence] = []
    covered: set[int] = set()
    index = 0
    while index < len(tokens):
        for size in (3, 2):
            key = tuple(tokens[index : index + size])
            entry = config.COMPOUND_TERMS.get(key)
            if entry is not None and len(key) == size:
                category, axis = entry
                evidence_items.append(
                    Evidence(category, axis, 0.95, f"compound term '{' '.join(key)}'")
                )
                covered.update(range(index, index + size))
                index += size - 1
                break
        index += 1
    return evidence_items, covered


def by_strong_token(tokens: list[str]) -> list[Evidence]:
    if not tokens:
        return []

    evidence_items, covered = _compound_evidence(tokens)

    edges = [(0, tokens[0], "leading")]
    if len(tokens) > 1:
        edges.append((len(tokens) - 1, tokens[-1], "trailing"))
    for position, token, label in edges:
        if position in covered:
            continue
        evidence_item = _edge_qualifier(token, label)
        if evidence_item is not None:
            evidence_items.append(evidence_item)

    for index, (word, expansion_confidence, original) in enumerate(expanded_tokens(tokens)):
        if index in covered:
            continue
        for category in current_context().strong_token_index.get(word, ()):
            token_weight = (
                config.QUALIFIER_TOKEN_WEIGHT
                if word in config.QUALIFIER_TOKENS
                else config.ENTITY_TOKEN_WEIGHT
            )
            weight = 0.85 * token_weight * expansion_confidence * _positional_weight(index)
            source = (
                f"token '{word}'" if word == original else f"abbreviation '{original}' → '{word}'"
            )
            evidence_items.append(Evidence(category, ROLE_AXIS, round(weight, 4), source))

    return evidence_items


def _truncation_factor(candidate: str, word: str) -> float:
    if len(candidate) >= len(word) or not word.startswith(candidate):
        return 1.0
    coverage = len(candidate) / len(word)
    return 1.0 if coverage > _MINIMUM_PREFIX_COVERAGE else coverage


def by_fuzzy(normalized_name: str, tokens: list[str]) -> list[Evidence]:
    matches: dict[str, tuple[float, str]] = {}

    name_candidates = [(normalized_name, 1.0, normalized_name)] + [
        c
        for c in expanded_tokens(tokens)
        if not (c[0] == c[2] and c[0] in current_context().strong_token_index)
    ]
    for category, keywords in current_context().fuzzy_categories.items():
        for word in keywords:
            normalized_word = normalize(word)
            threshold = (
                config.SHORT_FUZZY_THRESHOLD
                if len(normalized_word) <= 3
                else config.DEFAULT_FUZZY_THRESHOLD
            )
            for index, (candidate, confidence, original) in enumerate(name_candidates):
                normalized_candidate = normalize(candidate)
                similarity = JaroWinkler.similarity(normalized_candidate, normalized_word)
                if similarity < threshold:
                    continue
                similarity *= _truncation_factor(normalized_candidate, normalized_word)

                qualifier_weight = (
                    config.QUALIFIER_TOKEN_WEIGHT if original in config.QUALIFIER_TOKENS else 1.0
                )
                weight = (
                    0.8
                    * similarity
                    * confidence
                    * qualifier_weight
                    * _positional_weight(max(index - 1, 0))
                )
                current = matches.get(category)
                if current is None or weight > current[0]:
                    source = (
                        f"name similar to '{word}'"
                        if candidate == original
                        else f"abbreviation '{original}' → '{candidate}' ~ '{word}'"
                    )
                    matches[category] = (weight, source)

    return [
        Evidence(category, DOMAIN_AXIS, round(weight, 4), source)
        for category, (weight, source) in matches.items()
    ]


def by_structural_signature(profile: ContentProfile) -> list[Evidence]:
    evidence_items: list[Evidence] = []
    data_type = normalize_data_type(profile.data_type)

    if data_type == "Boolean":
        evidence_items.append(
            Evidence("Status / Indicator / Flag", ROLE_AXIS, 0.7, "boolean column")
        )

    if data_type == "Date":
        evidence_items.append(
            Evidence(config.DATE_CALENDAR_SEMANTIC, ROLE_AXIS, 0.7, "date-formatted values")
        )

    if (
        data_type == "Integer"
        and profile.monotonically_increasing
        and profile.uniqueness_ratio >= 0.99
    ):
        evidence_items.append(
            Evidence(
                config.IDENTIFIER_SEMANTIC,
                ROLE_AXIS,
                0.6,
                "unique increasing integer sequence",
            )
        )

    if (
        data_type == "Decimal"
        and profile.fixed_decimal_places == 2
        and profile.minimum is not None
        and profile.minimum >= 0
        and profile.skewness is not None
        and profile.skewness > 0.5
    ):
        evidence_items.append(
            Evidence(
                "Financial Value",
                ROLE_AXIS,
                0.45,
                "non-negative, right-skewed decimal with two places",
            )
        )

    if data_type == "Text" and profile.mean_string_length is not None:
        if profile.mean_string_length > 40 and profile.uniqueness_ratio > 0.5:
            evidence_items.append(
                Evidence(
                    "Free-form Text",
                    ROLE_AXIS,
                    0.55,
                    f"long text with {profile.mean_string_length:.0f} average characters",
                )
            )
        elif (
            profile.fixed_length
            and profile.uniqueness_ratio > 0.9
            and profile.distinct_count >= _MIN_DISTINCT_FOR_IDENTIFIER
        ):
            evidence_items.append(
                Evidence(
                    config.IDENTIFIER_SEMANTIC,
                    ROLE_AXIS,
                    0.5,
                    "fixed-length, near-unique text",
                )
            )

    return evidence_items


def by_table_context(tokens: list[str], table_domains: dict[str, float]) -> list[Evidence]:
    if not table_domains:
        return []

    evidence_items: list[Evidence] = []
    seen: set[str] = set()
    for word, confidence, original in expanded_tokens(tokens):
        if word == original or confidence >= 0.85:
            continue
        for category in current_context().strong_token_index.get(word, ()):
            key = f"{category}|{word}"
            if key in seen or category not in table_domains:
                continue
            seen.add(key)
            evidence_items.append(
                Evidence(
                    category,
                    ROLE_AXIS,
                    round(0.4 * table_domains[category], 4),
                    f"table context favors '{original}' → '{word}'",
                )
            )
        for category, strength in table_domains.items():
            if category not in current_context().fuzzy_categories:
                continue
            if word in current_context().fuzzy_categories[category]:
                key = f"{category}|{word}"
                if key in seen:
                    continue
                seen.add(key)
                evidence_items.append(
                    Evidence(
                        category,
                        DOMAIN_AXIS,
                        round(0.4 * strength, 4),
                        f"table context favors '{original}' → '{word}'",
                    )
                )
    return evidence_items


def profile_from_record(stats: dict[str, Any], sample: list[str]) -> ContentProfile:
    extra = stats.get("additional_statistics", {})
    return ContentProfile(
        data_type=stats.get("data_type", ""),
        distinct_values=sample,
        distinct_count=int(stats.get("distinct_values", 0)),
        uniqueness_ratio=float(stats.get("uniqueness_ratio", 0.0)),
        mean_string_length=extra.get("mean_string_length"),
        fixed_length=bool(extra.get("fixed_length", False)),
        skewness=extra.get("skewness"),
        minimum=extra.get("min"),
        monotonically_increasing=bool(stats.get("monotonically_increasing", False)),
        fixed_decimal_places=stats.get("fixed_decimal_places"),
    )
