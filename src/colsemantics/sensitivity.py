from .patterns import PATTERN_LABELS, canonical_pattern
from .results import Sensitivity

_PATTERN_RULES: dict[str, tuple[str, str]] = {
    "cpf": ("high", "mask"),
    "ssn": ("high", "mask"),
    "address": ("high", "mask"),
    "cnpj": ("medium", "review"),
    "ein": ("medium", "review"),
    "postal_code": ("medium", "review"),
}


def assess_sensitivity(semantic: str, detected_pattern: str) -> Sensitivity:
    pattern = canonical_pattern(detected_pattern)
    if pattern in _PATTERN_RULES:
        level, action = _PATTERN_RULES[pattern]
        label = PATTERN_LABELS.get(pattern, pattern)
        qualifier = "validated" if pattern in ("cpf", "cnpj", "ssn") else "detected"
        return {"level": level, "action": action, "reason": f"{qualifier} {label} pattern"}
    if semantic == "Person Name / Identifier":
        return {
            "level": "high",
            "action": "restrict",
            "reason": "person identity semantic",
        }
    if semantic == "Contact / Network":
        return {
            "level": "high",
            "action": "mask",
            "reason": "contact semantic",
        }
    if semantic == "Identifier (ID)":
        return {
            "level": "medium",
            "action": "review",
            "reason": "identifier semantic requires context",
        }
    return {
        "level": "none",
        "action": "allow",
        "reason": "no sensitive-data rule matched",
    }
