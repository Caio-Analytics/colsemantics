"""Load the word lists shipped in ``colsemantics/data``."""

from __future__ import annotations

from functools import cache
from importlib import resources


@cache
def load_wordlist(name: str) -> frozenset[str]:
    """Return the lines of ``data/<name>`` (already normalized: lowercase, no accents)."""
    text = resources.files("colsemantics").joinpath("data", name).read_text(encoding="utf-8")
    return frozenset(line for line in text.splitlines() if line)
