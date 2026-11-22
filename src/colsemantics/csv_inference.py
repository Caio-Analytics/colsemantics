from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .patterns import detect_column_pattern
from .profiles import temporary_profile

if TYPE_CHECKING:
    from . import ContentProfile

_CANDIDATE_DELIMITERS = (",", ";", "\t", "|")
DEFAULT_ENCODING = "utf-8-sig"


def _content_profile(values: list[str]) -> ContentProfile:
    from . import ContentProfile

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


def detect_delimiter(header_line: str) -> str:
    """Pick the candidate delimiter that splits the header into the most fields."""
    best, best_count = ",", 1
    for delimiter in _CANDIDATE_DELIMITERS:
        try:
            count = len(next(csv.reader([header_line], delimiter=delimiter)))
        except (csv.Error, StopIteration):
            continue
        if count > best_count:
            best, best_count = delimiter, count
    return best


def infer_csv(
    path: str | Path,
    *,
    sample_size: int = 10000,
    profile_name: str = "pt-BR",
    vocabulary_paths: str | None = None,
    encoding: str = DEFAULT_ENCODING,
    delimiter: str | None = None,
) -> dict[str, Any]:
    """Infer column semantics from a bounded CSV sample.

    ``delimiter=None`` detects ``,``, ``;``, tab, or ``|`` from the header line.
    """
    from . import infer_table

    if sample_size <= 0:
        raise ValueError("sample_size must be greater than zero.")
    if delimiter is not None and len(delimiter) != 1:
        raise ValueError("delimiter must be a single character.")

    source_path = Path(path)
    try:
        with source_path.open(encoding=encoding, newline="") as source:
            used_delimiter = delimiter or detect_delimiter(source.readline())
            source.seek(0)
            reader = csv.DictReader(source, delimiter=used_delimiter)
            headers = reader.fieldnames
            if not headers or any(not header or not header.strip() for header in headers):
                raise ValueError("CSV input must include a non-empty header row.")
            rows = []
            for row in reader:
                rows.append(row)
                if len(rows) == sample_size:
                    break
    except UnicodeDecodeError as error:
        raise ValueError(
            f"Could not decode {source_path} as '{encoding}'. "
            "Pass the file's real encoding (for example 'latin-1' or 'cp1252')."
        ) from error

    columns_input = []
    for header in headers:
        values = [str(row.get(header, "")) for row in rows if row.get(header) not in (None, "")]
        columns_input.append(
            {
                "column_name": header,
                "profile": _content_profile(values),
                "detected_pattern": detect_column_pattern(values),
            }
        )

    with temporary_profile(profile_name, vocabulary_paths):
        columns = infer_table(columns_input)
    for index, (column, header) in enumerate(zip(columns, headers, strict=True)):
        column["column_name"] = header
        column["column_index"] = index
    summary = dict(sorted(Counter(str(column["semantic"]) for column in columns).items()))
    return {
        "source": {
            "path": str(source_path),
            "format": "csv",
            "encoding": encoding,
            "delimiter": used_delimiter,
        },
        "profile": profile_name,
        "sample_size": sample_size,
        "rows_sampled": len(rows),
        "columns": columns,
        "summary": summary,
    }
