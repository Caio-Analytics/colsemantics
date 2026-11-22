import re

from unidecode import unidecode

from ._data import load_wordlist
from .context import current_context
from .vocabulary import ABBREVIATIONS

_RE_CAMEL = re.compile(r"([a-z0-9])([A-Z])")
_RE_SEPARATORS = re.compile(r"[\W_]+")
_RE_LETTER_DIGIT = re.compile(r"([a-z])(\d)")


_MAX_EXPANSION_RATIO = 4.0
_MIN_ABBREVIATION_LEN = 2


_MIN_SPECULATIVE_ABBREVIATION_LEN = 3


def normalize(text: str) -> str:
    return unidecode(str(text)).lower().strip()


# Fused, lower-case column names such as ``issueddate``, ``datecreated`` or ``objectid`` are split
# when one part is a head word and the other a modifier seen in public column names.
_TRAILING_HEADS = ("datetime", "timestamp", "date", "time", "id", "code", "number", "name", "year")
_LEADING_HEADS = ("datetime", "date", "time", "fecha")
_PAST_PARTICIPLES = frozenset(
    {"created", "updated", "modified", "entered", "posted", "closed", "opened", "issued"}
)
_EXTRA_LEADING_REST = frozenset({"asof", "extract", "export", "dispatch", "arrive", "create"})
_MIN_FUSED_LENGTH = 6
_MIN_MODIFIER_LENGTH = 3


def _split_fused(token: str) -> list[str]:
    """Split ``issueddate`` into ``issued date`` when the other part is a known modifier."""
    if len(token) < _MIN_FUSED_LENGTH or not token.isalpha():
        return [token]
    modifiers = load_wordlist("modifiers.txt")
    for head in _TRAILING_HEADS:
        prefix = token[: -len(head)]
        if token.endswith(head) and len(prefix) >= _MIN_MODIFIER_LENGTH and prefix in modifiers:
            return [*_split_fused(prefix), head]
    for head in _LEADING_HEADS:
        rest = token[len(head) :]
        known = rest in modifiers or rest in _PAST_PARTICIPLES or rest in _EXTRA_LEADING_REST
        if token.startswith(head) and len(rest) >= _MIN_MODIFIER_LENGTH + 1 and known:
            return [head, rest]
    if token.startswith("data") and token[4:] in _EXTRA_LEADING_REST | _PAST_PARTICIPLES:
        return ["data", token[4:]]
    if token.endswith("flag") and len(token) >= len("flag") + 3:
        return [token[:-4], "flag"]
    for suffix in ("on", "date"):
        prefix = token[: -len(suffix)]
        if token.endswith(suffix) and prefix in _PAST_PARTICIPLES:
            return [prefix, "date"]
    for participle in ("updated", "modified", "created"):
        if token.endswith(participle) and token[: -len(participle)] in ("last", "date"):
            return [token[: -len(participle)], participle]
    return [token]


def tokenize(column_name: str) -> list[str]:
    name = _RE_CAMEL.sub(r"\1_\2", str(column_name))
    name = normalize(name)
    name = _RE_LETTER_DIGIT.sub(r"\1_\2", name)
    tokens: list[str] = []
    for part in _RE_SEPARATORS.split(name):
        if part:
            tokens.extend(_split_fused(part))
    return tokens


def _expansion_vocabulary() -> tuple[str, ...]:
    return current_context().abbreviation_words


def _is_subsequence(abbreviation: str, word: str) -> bool:
    iterator = iter(word)
    return all(letter in iterator for letter in abbreviation)


def expand_abbreviation(token: str) -> tuple[tuple[str, float], ...]:
    if len(token) < _MIN_ABBREVIATION_LEN or not token.isalpha():
        return ()

    if token in _expansion_vocabulary():
        return ()

    curated = ABBREVIATIONS.get(token)
    if curated:
        confidence = 0.85 if len(curated) == 1 else 0.55
        return tuple((word, confidence) for word in curated)

    if len(token) < _MIN_SPECULATIVE_ABBREVIATION_LEN:
        return ()

    candidates: list[tuple[str, float]] = []
    for word in _expansion_vocabulary():
        if word == token or len(word) <= len(token):
            continue
        if len(word) > len(token) * _MAX_EXPANSION_RATIO:
            continue
        if word[0] != token[0]:
            continue
        if not _is_subsequence(token, word):
            continue

        coverage = len(token) / len(word)
        candidates.append((word, round(0.35 + 0.35 * coverage, 4)))

    candidates.sort(key=lambda c: -c[1])
    return tuple(candidates[:3])


def expanded_tokens(tokens: list[str]) -> list[tuple[str, float, str]]:
    result: list[tuple[str, float, str]] = []
    for token in tokens:
        result.append((token, 1.0, token))
        for word, confidence in expand_abbreviation(token):
            if word != token:
                result.append((word, confidence, token))
    return result
