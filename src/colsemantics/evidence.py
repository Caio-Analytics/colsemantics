from dataclasses import dataclass
from typing import Any

ROLE_AXIS = "role"
DOMAIN_AXIS = "domain"


_CONCLUSIVE_MARGIN = 0.15


@dataclass(frozen=True)
class Evidence:
    category: str
    axis: str
    weight: float
    source: str


def _noisy_or(weights: list[float]) -> float:
    result = 1.0
    for weight in weights:
        result *= 1.0 - max(0.0, min(1.0, weight))
    return 1.0 - result


def rank(evidence_items: list[Evidence], axis: str) -> list[dict[str, Any]]:
    by_category: dict[str, list[Evidence]] = {}
    for evidence_item in evidence_items:
        if evidence_item.axis == axis:
            by_category.setdefault(evidence_item.category, []).append(evidence_item)

    ranking: list[dict[str, Any]] = [
        {
            "category": category,
            "confidence": round(_noisy_or([e.weight for e in items]), 4),
            "sources": [e.source for e in sorted(items, key=lambda e: -e.weight)],
        }
        for category, items in by_category.items()
    ]
    ranking.sort(key=lambda r: -float(r["confidence"]))
    return ranking


def choose(ranking: list[dict[str, Any]]) -> tuple[str | None, float, str, bool]:
    if not ranking:
        return None, 0.0, "No evidence", False
    winner = ranking[0]
    margin = winner["confidence"] - (ranking[1]["confidence"] if len(ranking) > 1 else 0.0)
    return (
        winner["category"],
        float(winner["confidence"]),
        " + ".join(winner["sources"][:3]),
        bool(margin >= _CONCLUSIVE_MARGIN),
    )
