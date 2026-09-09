import csv
from collections import Counter
from pathlib import Path
from typing import Any

from . import ContentProfile, infer_table
from .profiles import temporary_profile


def _content_profile(values: list[str]) -> ContentProfile:
    distinct_values = sorted(set(values))
    mean_string_length = sum(len(value) for value in values) / len(values) if values else None
    return ContentProfile(
        data_type="Text",
        distinct_values=distinct_values,
        distinct_count=len(distinct_values),
        uniqueness_ratio=len(distinct_values) / len(values) if values else 0.0,
        mean_string_length=mean_string_length,
        fixed_length=len({len(value) for value in values}) == 1 if values else False,
    )


def infer_csv(
    path: str | Path,
    *,
    sample_size: int = 10000,
    profile_name: str = "pt-BR",
    vocabulary_paths: str | None = None,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    if sample_size <= 0:
        raise ValueError("sample_size must be greater than zero.")

    source_path = Path(path)
    with source_path.open(encoding=encoding, newline="") as source:
        reader = csv.DictReader(source)
        headers = reader.fieldnames
        if not headers or any(not header or not header.strip() for header in headers):
            raise ValueError("CSV input must include a non-empty header row.")
        rows = []
        for row in reader:
            rows.append(row)
            if len(rows) == sample_size:
                break

    profiles = []
    for header in headers:
        values = [str(row.get(header, "")) for row in rows if row.get(header) not in (None, "")]
        profiles.append({"column_name": header, "profile": _content_profile(values)})

    with temporary_profile(profile_name, vocabulary_paths):
        columns = infer_table(profiles)
    summary = dict(sorted(Counter(str(column["semantic"]) for column in columns).items()))
    return {
        "source": {"path": str(source_path), "format": "csv", "encoding": encoding},
        "profile": profile_name,
        "sample_size": sample_size,
        "rows_sampled": len(rows),
        "columns": columns,
        "summary": summary,
    }
