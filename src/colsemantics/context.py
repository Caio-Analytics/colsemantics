from __future__ import annotations

from collections.abc import Mapping
from contextvars import ContextVar, Token
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from . import _taxonomy as taxonomy
from .vocabulary import ABBREVIATIONS, GAZETTEERS


@dataclass(frozen=True)
class SemanticContext:
    profile_name: str
    strong_categories: Mapping[str, tuple[str, ...]]
    fuzzy_categories: Mapping[str, tuple[str, ...]]
    gazetteers: tuple[Mapping[str, Any], ...]
    strong_token_index: Mapping[str, tuple[str, ...]]
    abbreviation_words: tuple[str, ...]
    column_overrides: Mapping[str, str]


def create_context(
    profile_name: str = "pt-BR",
    strong_categories: Mapping[str, tuple[str, ...]] | None = None,
    fuzzy_categories: Mapping[str, tuple[str, ...]] | None = None,
    gazetteers: tuple[Mapping[str, Any], ...] | None = None,
    column_overrides: Mapping[str, str] | None = None,
) -> SemanticContext:
    strong = strong_categories or {
        category: tuple(terms) for category, terms in taxonomy.STRONG_CATEGORIES.items()
    }
    fuzzy = fuzzy_categories or {
        category: tuple(terms) for category, terms in taxonomy.FUZZY_CATEGORIES.items()
    }
    sources = gazetteers or tuple(GAZETTEERS)
    index: dict[str, list[str]] = {}
    for category, terms in strong.items():
        for term in terms:
            index.setdefault(term, []).append(category)
    words = {word for terms in strong.values() for word in terms}
    words.update(word for terms in fuzzy.values() for word in terms)
    words.update(word for expansions in ABBREVIATIONS.values() for word in expansions)
    return SemanticContext(
        profile_name=profile_name,
        strong_categories=MappingProxyType(dict(strong)),
        fuzzy_categories=MappingProxyType(dict(fuzzy)),
        gazetteers=tuple(
            MappingProxyType({**item, "values": frozenset(item["values"])}) for item in sources
        ),
        strong_token_index=MappingProxyType({key: tuple(value) for key, value in index.items()}),
        abbreviation_words=tuple(sorted(words)),
        column_overrides=MappingProxyType(dict(column_overrides or {})),
    )


_DEFAULT_CONTEXT = create_context()
_CURRENT_CONTEXT: ContextVar[SemanticContext] = ContextVar(
    "colsemantics_context", default=_DEFAULT_CONTEXT
)


def current_context() -> SemanticContext:
    return _CURRENT_CONTEXT.get()


def set_context(context: SemanticContext) -> Token[SemanticContext]:
    return _CURRENT_CONTEXT.set(context)


def reset_context(token: Token[SemanticContext]) -> None:
    _CURRENT_CONTEXT.reset(token)
