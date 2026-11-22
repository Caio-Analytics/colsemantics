from collections.abc import Iterator
from contextlib import contextmanager

from .context import SemanticContext, create_context, reset_context, set_context
from .vocabularies import load_vocabularies

DEFAULT_PROFILE = "pt-BR"
_PROFILES = {DEFAULT_PROFILE: create_context(DEFAULT_PROFILE)}


def available_profiles() -> tuple[str, ...]:
    """Names of the embedded vocabulary profiles (currently ``pt-BR``)."""
    return tuple(_PROFILES)


def load_profile(
    name: str = DEFAULT_PROFILE, vocabulary_paths: str | None = None
) -> SemanticContext:
    """Build the context for an embedded profile, optionally extended by YAML vocabularies.

    Args:
        name: An embedded profile name, see ``available_profiles``.
        vocabulary_paths: Comma-separated YAML files with ``strong_categories``,
            ``fuzzy_categories``, ``gazetteers``, and ``column_overrides``.

    Raises:
        ValueError: Unknown profile or invalid vocabulary file.
    """
    try:
        base_context = _PROFILES[name]
    except KeyError as error:
        available = ", ".join(available_profiles())
        raise ValueError(f"Unknown profile '{name}'. Available profiles: {available}.") from error
    return load_vocabularies(vocabulary_paths, base_context)


@contextmanager
def temporary_profile(
    name: str = DEFAULT_PROFILE, vocabulary_paths: str | None = None
) -> Iterator[None]:
    """Context manager that applies a profile (and YAML vocabularies) inside the ``with``
    block only. Scoped with ``ContextVar``, so concurrent analyses stay isolated.
    """
    token = set_context(load_profile(name, vocabulary_paths))
    try:
        yield
    finally:
        reset_context(token)
