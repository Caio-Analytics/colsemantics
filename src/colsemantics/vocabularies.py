from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import yaml

from .context import SemanticContext, create_context, current_context, reset_context, set_context


@contextmanager
def temporary_vocabulary(paths: str | None) -> Iterator[None]:
    if not paths:
        yield
        return
    token = set_context(load_vocabularies(paths, current_context()))
    try:
        yield
    finally:
        reset_context(token)


def load_vocabularies(paths: str | None, base: SemanticContext | None = None) -> SemanticContext:
    context = base or current_context()
    strong = {category: tuple(terms) for category, terms in context.strong_categories.items()}
    fuzzy = {category: tuple(terms) for category, terms in context.fuzzy_categories.items()}
    gazetteers: list[dict[str, object]] = [
        {**item, "valores": set(item["valores"])} for item in context.gazetteers
    ]
    overrides = dict(context.column_overrides)
    if not paths:
        return create_context(strong, fuzzy, tuple(gazetteers), overrides)
    for path in (Path(value.strip()) for value in paths.split(",") if value.strip()):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Vocabulary '{path}' must be a YAML mapping.")
        for key, destination in (("strong_categories", strong), ("fuzzy_categories", fuzzy)):
            sections = data.get(key, {})
            if not isinstance(sections, dict):
                raise ValueError(f"'{key}' in '{path}' must map categories to term lists.")
            for category, terms in sections.items():
                if not isinstance(terms, list) or not all(isinstance(term, str) for term in terms):
                    raise ValueError(f"Terms for '{category}' in '{path}' must be strings.")
                destination[str(category)] = tuple(
                    destination.get(str(category), ()) + tuple(terms)
                )
        extra_gazetteers = data.get("gazetteers", [])
        if not isinstance(extra_gazetteers, list):
            raise ValueError(f"'gazetteers' in '{path}' must be a list.")
        for item in extra_gazetteers:
            if (
                not isinstance(item, dict)
                or not {"name", "values", "category", "axis"} <= item.keys()
            ):
                raise ValueError(f"Invalid gazetteer in '{path}'.")
            values = item["values"]
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                raise ValueError(f"Gazetteer values in '{path}' must be strings.")
            gazetteers.append(
                {
                    "nome": str(item["name"]),
                    "valores": set(values),
                    "categoria": str(item["category"]),
                    "eixo": str(item["axis"]),
                    "cobertura_minima": float(item.get("minimum_coverage", 0.8)),
                    "peso": float(item.get("weight", 0.8)),
                    "max_distintos": int(item.get("max_distinct", 100)),
                }
            )
        file_overrides = data.get("column_overrides", {})
        if not isinstance(file_overrides, dict) or not all(
            isinstance(column, str) and isinstance(category, str)
            for column, category in file_overrides.items()
        ):
            raise ValueError(f"'column_overrides' in '{path}' must map column names to categories.")
        overrides.update(file_overrides)
    return create_context(strong, fuzzy, tuple(gazetteers), overrides)


def export_overrides_template(payload: dict[str, Any], path: str) -> None:
    overrides = {
        str(column["column"]): str(column["semantic"]) for column in payload.get("columns", [])
    }
    Path(path).write_text(
        yaml.safe_dump({"column_overrides": overrides}, allow_unicode=True, sort_keys=True),
        encoding="utf-8",
    )
