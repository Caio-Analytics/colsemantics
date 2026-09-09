from collections.abc import Iterator
from contextlib import contextmanager

from .context import SemanticContext, create_context, reset_context, set_context
from .vocabularies import load_vocabularies

_PROFILES = {"pt-BR": create_context()}


def available_profiles() -> tuple[str, ...]:
    return tuple(_PROFILES)


def load_profile(
    name: str = "pt-BR", vocabulary_paths: str | None = None
) -> SemanticContext:
    try:
        base_context = _PROFILES[name]
    except KeyError as error:
        available = ", ".join(available_profiles())
        raise ValueError(f"Unknown profile '{name}'. Available profiles: {available}.") from error
    return load_vocabularies(vocabulary_paths, base_context)


@contextmanager
def temporary_profile(
    name: str = "pt-BR", vocabulary_paths: str | None = None
) -> Iterator[None]:
    token = set_context(load_profile(name, vocabulary_paths))
    try:
        yield
    finally:
        reset_context(token)
