import re

from unidecode import unidecode

from .context import current_context
from .vocabulary import ABBREVIATIONS

_RE_CAMEL = re.compile(r"([a-z0-9])([A-Z])")
_RE_SEPARADORES = re.compile(r"[_\s\-\.]+")
_RE_LETRA_NUMERO = re.compile(r"([a-z])(\d)")


_RAZAO_MAX_EXPANSAO = 4.0
_MIN_LEN_ABREVIATURA = 2


_MIN_LEN_ABREVIATURA_ESPECULATIVA = 3


def normalizar(text: str) -> str:
    return unidecode(str(text)).lower().strip()


def tokenizar(column_name: str) -> list[str]:
    name = _RE_CAMEL.sub(r"\1_\2", str(column_name))
    name = normalizar(name)
    name = _RE_LETRA_NUMERO.sub(r"\1_\2", name)
    return [p for p in _RE_SEPARADORES.split(name) if p]


def _expansion_vocabulary() -> tuple[str, ...]:
    return current_context().abbreviation_words


def _is_subsequence(abbreviation: str, word: str) -> bool:
    iterator = iter(word)
    return all(letter in iterator for letter in abbreviation)


def expand_abbreviation(token: str) -> tuple[tuple[str, float], ...]:
    if len(token) < _MIN_LEN_ABREVIATURA or not token.isalpha():
        return ()

    if token in _expansion_vocabulary():
        return ()

    curated = ABBREVIATIONS.get(token)
    if curated:
        confidence = 0.85 if len(curated) == 1 else 0.55
        return tuple((word, confidence) for word in curated)

    if len(token) < _MIN_LEN_ABREVIATURA_ESPECULATIVA:
        return ()

    candidates: list[tuple[str, float]] = []
    for word in _expansion_vocabulary():
        if word == token or len(word) <= len(token):
            continue
        if len(word) > len(token) * _RAZAO_MAX_EXPANSAO:
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
