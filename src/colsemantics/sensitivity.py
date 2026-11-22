from .patterns import canonical_pattern
from .results import Sensitivity


def assess_sensitivity(semantic: str, detected_pattern: str) -> Sensitivity:
    detected_pattern = canonical_pattern(detected_pattern)
    if detected_pattern == "cpf":
        return {
            "level": "high",
            "action": "mask",
            "reason": "validated CPF pattern",
        }
    if detected_pattern == "cnpj":
        return {
            "level": "medium",
            "action": "review",
            "reason": "validated CNPJ pattern",
        }
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
