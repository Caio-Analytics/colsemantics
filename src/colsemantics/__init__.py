import warnings
from typing import Any

from . import _taxonomy as config
from .calibration import calibrate, requires_review
from .context import SemanticContext, current_context
from .csv_inference import infer_csv
from .detectors import (
    STRUCTURAL_ROLES,
    ContentProfile,
    by_content_pattern,
    by_fuzzy,
    by_gazetteer,
    by_strong_token,
    by_structural_signature,
    by_table_context,
)
from .evidence import DOMAIN_AXIS, ROLE_AXIS, Evidence, choose, rank
from .patterns import NO_PATTERN, PATTERN_LABELS, analyze_values, canonical_pattern
from .profiles import available_profiles, load_profile, temporary_profile
from .results import (
    CsvColumnResult,
    CsvReport,
    Hypothesis,
    InferenceResult,
    PatternInfo,
    Sensitivity,
)
from .sensitivity import assess_sensitivity
from .tokens import normalize, tokenize
from .vocabularies import export_overrides_template, load_vocabularies, temporary_vocabulary

__version__ = "0.3.1"

__all__ = [
    "ContentProfile",
    "CsvColumnResult",
    "CsvReport",
    "Hypothesis",
    "InferenceResult",
    "PatternInfo",
    "SemanticContext",
    "Sensitivity",
    "assess_sensitivity",
    "available_profiles",
    "calibrate",
    "current_context",
    "export_overrides_template",
    "infer_column",
    "infer_csv",
    "infer_table",
    "load_profile",
    "load_vocabularies",
    "normalize",
    "requires_review",
    "temporary_profile",
    "temporary_vocabulary",
    "tokenize",
]

_DEPRECATED_ALIASES = {"normalizar": "normalize", "tokenizar": "tokenize"}


def __getattr__(name: str) -> Any:
    if name in _DEPRECATED_ALIASES:
        replacement = _DEPRECATED_ALIASES[name]
        warnings.warn(
            f"colsemantics.{name} is deprecated and will be removed in 1.0; use colsemantics.{replacement}",
            DeprecationWarning,
            stacklevel=2,
        )
        return globals()[replacement]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


_CONTEXT_MINIMUM_CONFIDENCE = 0.7
_DOMAIN_MINIMUM_CONFIDENCE = 0.5
_MAX_HYPOTHESES = 4
# A strong domain (for example an address pattern in the values) beats a weak structural
# role guessed from an uninformative column name.
_CONTENT_DOMAIN_CONFIDENCE = 0.85
_CONTENT_DOMAIN_MARGIN = 0.3


def _resolve_pattern(detected_pattern: str, profile: ContentProfile | None) -> PatternInfo | None:
    """Combine a caller-reported pattern with what the sampled values actually look like."""
    reported = canonical_pattern(detected_pattern)
    expected = None if reported == NO_PATTERN else reported
    found = (
        analyze_values(profile.distinct_values, expected_type=expected)
        if profile is not None and profile.distinct_values
        else None
    )
    if found is not None or expected is None:
        return found
    label = PATTERN_LABELS.get(expected, expected)
    return {
        "type": expected,
        "locale": None,
        "variant": None,
        "format": None,
        "coverage": None,
        "validated": True,
        "message": f"validated {label} pattern",
    }


def _collect_evidence(
    column_name: str, pattern: PatternInfo | None, profile: ContentProfile | None
) -> list[Evidence]:
    tokens = tokenize(column_name)
    normalized_name = normalize(column_name)
    evidence_items = (
        by_content_pattern(pattern) + by_strong_token(tokens) + by_fuzzy(normalized_name, tokens)
    )
    if profile is not None:
        evidence_items += by_gazetteer(profile) + by_structural_signature(profile)
    return evidence_items


def _refine_role(
    role: str | None, domain: str | None, profile: ContentProfile | None
) -> str | None:
    if (
        role == config.PERSON_NAME_SEMANTIC
        and domain is not None
        and domain not in config.PERSON_DOMAINS
    ):
        return config.ENTITY_LABEL_SEMANTIC
    if role == config.FREE_FORM_TEXT_SEMANTIC and profile is not None:
        is_dimension_cardinality = (
            1 < profile.distinct_count <= config.MAX_CATEGORY_CARDINALITY
            and profile.uniqueness_ratio < 0.5
        )
        if is_dimension_cardinality:
            return config.CATEGORY_SEMANTIC
    return role


def _build_result(
    evidence_items: list[Evidence],
    profile: ContentProfile | None = None,
    pattern: PatternInfo | None = None,
) -> InferenceResult:
    role_ranking = rank(evidence_items, ROLE_AXIS)
    domain_ranking = rank(evidence_items, DOMAIN_AXIS)
    role, role_confidence, role_source, role_conclusive = choose(role_ranking)
    domain, domain_confidence, domain_source, _ = choose(domain_ranking)
    uncertain_domain = domain is not None and domain_confidence < _DOMAIN_MINIMUM_CONFIDENCE
    if uncertain_domain:
        domain, domain_confidence, domain_source = None, 0.0, "No evidence"
    role = _refine_role(role, domain, profile)
    content_domain_wins = (
        domain is not None
        and domain_confidence >= _CONTENT_DOMAIN_CONFIDENCE
        and role_confidence < domain_confidence - _CONTENT_DOMAIN_MARGIN
    )
    if role in STRUCTURAL_ROLES and not content_domain_wins:
        semantic, raw_confidence, source = role, role_confidence, role_source
    elif domain is not None:
        semantic, raw_confidence, source = domain, domain_confidence, domain_source
    elif role is not None:
        semantic, raw_confidence, source = role, role_confidence, role_source
    else:
        semantic, raw_confidence, source = config.GENERIC_SEMANTIC, 0.0, "Unmatched"
    candidates: list[Hypothesis] = [
        {
            "semantic": item["category"],
            "axis": axis,
            "confidence": item["confidence"],
            "evidence": item["sources"][:3],
        }
        for axis, ranking in ((ROLE_AXIS, role_ranking), (DOMAIN_AXIS, domain_ranking))
        for item in ranking
    ]
    hypotheses = sorted(candidates, key=lambda hypothesis: -hypothesis["confidence"])[
        :_MAX_HYPOTHESES
    ]
    confidence = calibrate(round(raw_confidence, 4), current_context().profile_name)
    return {
        "semantic": semantic,
        "role": role,
        "domain": domain,
        "raw_confidence": round(raw_confidence, 4),
        "confidence": confidence,
        "evidence": source,
        "conclusive": not (bool(role_ranking) and not role_conclusive) and not uncertain_domain,
        "review_required": requires_review(confidence),
        "sensitivity": assess_sensitivity(semantic, pattern["type"] if pattern else NO_PATTERN),
        "pattern": pattern,
        "hypotheses": hypotheses,
    }


def _column_evidence(
    name: str, pattern: PatternInfo | None, profile: ContentProfile | None
) -> tuple[list[Evidence], bool]:
    """Return the evidence for a column and whether a vocabulary override decided it."""
    override = current_context().column_overrides.get(name)
    if override:
        axis = ROLE_AXIS if override in STRUCTURAL_ROLES else DOMAIN_AXIS
        return [Evidence(override, axis, 1.0, "vocabulary override")], True
    return _collect_evidence(name, pattern, profile), False


def _infer_one(
    name: str, detected_pattern: str, profile: ContentProfile | None
) -> tuple[InferenceResult, list[Evidence]]:
    pattern = _resolve_pattern(detected_pattern, profile)
    evidence_items, overridden = _column_evidence(name, pattern, profile)
    result = _build_result(evidence_items, profile, pattern)
    if overridden:
        result["conclusive"] = True
    return result, evidence_items


def infer_column(
    column_name: str, detected_pattern: str = "None", profile: ContentProfile | None = None
) -> InferenceResult:
    return _infer_one(column_name, detected_pattern, profile)[0]


def _column_name(column: dict[str, Any], position: int) -> str:
    name = column.get("column_name", column.get("name"))
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"Column at position {position} requires a non-empty 'column_name'.")
    return name


def _column_profile(column: dict[str, Any]) -> ContentProfile | None:
    profile = column.get("profile")
    if profile is not None and not isinstance(profile, ContentProfile):
        raise TypeError("profile must be a ContentProfile instance")
    return profile


def infer_table(columns: list[dict[str, Any]]) -> list[InferenceResult]:
    parsed = [
        (
            _column_name(column, position),
            str(column.get("detected_pattern", column.get("pattern", NO_PATTERN))),
            _column_profile(column),
        )
        for position, column in enumerate(columns)
    ]
    first_pass = [_infer_one(name, pattern, profile) for name, pattern, profile in parsed]
    results = [result for result, _ in first_pass]
    table_domains = _subject_profile(results)
    if not table_domains:
        return results
    for index, ((name, _pattern, profile), (result, evidence_items)) in enumerate(
        zip(parsed, first_pass, strict=True)
    ):
        if result["conclusive"]:
            continue
        extras = by_table_context(tokenize(name), table_domains)
        if extras:
            results[index] = _build_result(evidence_items + extras, profile, result["pattern"])
    return results


def _subject_profile(results: list[InferenceResult]) -> dict[str, float]:
    strengths: dict[str, float] = {}
    for result in results:
        if not result["conclusive"]:
            continue
        for category in (result["role"], result["domain"]):
            if (
                category
                and category != config.GENERIC_SEMANTIC
                and result["raw_confidence"] >= _CONTEXT_MINIMUM_CONFIDENCE
            ):
                strengths[category] = max(strengths.get(category, 0.0), result["raw_confidence"])
    return strengths
