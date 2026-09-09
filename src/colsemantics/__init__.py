from typing import Any

from . import _taxonomy as config
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
from .profiles import available_profiles, load_profile, temporary_profile
from .tokens import normalizar, tokenizar
from .vocabularies import export_overrides_template, load_vocabularies, temporary_vocabulary

__version__ = "0.3.0"

__all__ = [
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

_CONTEXT_MINIMUM_CONFIDENCE = 0.7
_DOMAIN_MINIMUM_CONFIDENCE = 0.5
_MAX_HYPOTHESES = 4


def _collect_evidence(column_name: str, detected_pattern: str, profile: ContentProfile | None) -> list[Evidence]:
    tokens = tokenizar(column_name)
    normalized_name = normalizar(column_name)
    evidence_items = by_content_pattern(detected_pattern) + by_strong_token(tokens) + by_fuzzy(normalized_name, tokens)
    if profile is not None:
        evidence_items += by_gazetteer(profile) + by_structural_signature(profile)
    return evidence_items


def _refine_role(role: str | None, domain: str | None, profile: ContentProfile | None) -> str | None:
    if role == config.PERSON_NAME_SEMANTIC and domain is not None and domain not in config.PERSON_DOMAINS:
        return config.ENTITY_LABEL_SEMANTIC
    if role == config.FREE_FORM_TEXT_SEMANTIC and profile is not None:
        is_dimension_cardinality = 1 < profile.distinct_count <= config.MAX_CATEGORY_CARDINALITY and profile.uniqueness_ratio < 0.5
        if is_dimension_cardinality:
            return config.CATEGORY_SEMANTIC
    return role


def _build_result(evidence_items: list[Evidence], profile: ContentProfile | None = None) -> dict[str, Any]:
    role_ranking = rank(evidence_items, ROLE_AXIS)
    domain_ranking = rank(evidence_items, DOMAIN_AXIS)
    role, role_confidence, role_source, role_conclusive = choose(role_ranking)
    domain, domain_confidence, domain_source, _ = choose(domain_ranking)
    uncertain_domain = domain is not None and domain_confidence < _DOMAIN_MINIMUM_CONFIDENCE
    if uncertain_domain:
        domain, domain_confidence, domain_source = None, 0.0, "No evidence"
    role = _refine_role(role, domain, profile)
    if role in STRUCTURAL_ROLES:
        semantic, raw_confidence, source = role, role_confidence, role_source
    elif domain is not None:
        semantic, raw_confidence, source = domain, domain_confidence, domain_source
    elif role is not None:
        semantic, raw_confidence, source = role, role_confidence, role_source
    else:
        semantic, raw_confidence, source = config.GENERIC_SEMANTIC, 0.0, "Unmatched"
    hypotheses = sorted(
        [
            {"semantic": item["category"], "axis": axis, "confidence": item["confidence"], "evidence": item["sources"][:3]}
            for axis, ranking in ((ROLE_AXIS, role_ranking), (DOMAIN_AXIS, domain_ranking))
            for item in ranking
        ],
        key=lambda hypothesis: -hypothesis["confidence"],
    )[:_MAX_HYPOTHESES]
    return {
        "semantic": semantic,
        "role": role,
        "domain": domain,
        "raw_confidence": round(raw_confidence, 4),
        "confidence": round(raw_confidence, 4),
        "evidence": source,
        "conclusive": not (bool(role_ranking) and not role_conclusive) and not uncertain_domain,
        "hypotheses": hypotheses,
    }


def infer_column(column_name: str, detected_pattern: str = "None", profile: ContentProfile | None = None) -> dict[str, Any]:
    override = current_context().column_overrides.get(column_name)
    if override:
        axis = ROLE_AXIS if override in STRUCTURAL_ROLES else DOMAIN_AXIS
        result = _build_result([Evidence(override, axis, 1.0, "vocabulary override")], profile)
        result["conclusive"] = True
        return result
    return _build_result(_collect_evidence(column_name, detected_pattern, profile), profile)


def infer_table(columns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence_by_column: list[list[Evidence]] = []
    results: list[dict[str, Any]] = []
    for column in columns:
        name = str(column.get("column_name", column.get("name")))
        profile = column.get("profile")
        if profile is not None and not isinstance(profile, ContentProfile):
            raise TypeError("profile must be a ContentProfile instance")
        override = current_context().column_overrides.get(name)
        evidence_items = [Evidence(override, ROLE_AXIS if override in STRUCTURAL_ROLES else DOMAIN_AXIS, 1.0, "vocabulary override")] if override else _collect_evidence(name, str(column.get("detected_pattern", column.get("pattern", "None"))), profile)
        evidence_by_column.append(evidence_items)
        result = _build_result(evidence_items, profile)
        if override:
            result["conclusive"] = True
        results.append(result)
    table_domains = _subject_profile(results)
    if not table_domains:
        return results
    for index, (column, result) in enumerate(zip(columns, results, strict=True)):
        if result["conclusive"]:
            continue
        name = str(column.get("column_name", column.get("name")))
        extras = by_table_context(tokenizar(name), table_domains)
        if extras:
            results[index] = _build_result(evidence_by_column[index] + extras, column.get("profile"))
    return results


def _subject_profile(results: list[dict[str, Any]]) -> dict[str, float]:
    strengths: dict[str, float] = {}
    for result in results:
        if not result["conclusive"]:
            continue
        for category in (result["role"], result["domain"]):
            if category and category != config.GENERIC_SEMANTIC and result["raw_confidence"] >= _CONTEXT_MINIMUM_CONFIDENCE:
                strengths[category] = max(strengths.get(category, 0.0), result["raw_confidence"])
    return strengths
