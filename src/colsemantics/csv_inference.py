from __future__ import annotations

import csv
import random
from collections import Counter
from pathlib import Path
from typing import Literal

from .patterns import detect_column_pattern
from .profiles import temporary_profile
from .profiling import profile_values
from .results import CsvColumnResult, CsvReport

_CANDIDATE_DELIMITERS = (",", ";", "\t", "|")
DEFAULT_ENCODING = "utf-8-sig"


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


def _duplicate_header_warnings(headers: list[str]) -> list[str]:
    positions: dict[str, list[int]] = {}
    for position, header in enumerate(headers):
        positions.setdefault(header, []).append(position)
    return [
        f"Header '{header}' appears in columns {', '.join(map(str, where))}; each is analyzed separately."
        for header, where in positions.items()
        if len(where) > 1
    ]


def infer_csv(
    path: str | Path,
    *,
    sample_size: int = 10000,
    profile_name: str = "pt-BR",
    vocabulary_paths: str | None = None,
    encoding: str = DEFAULT_ENCODING,
    delimiter: str | None = None,
    sampling: Literal["reservoir", "head"] = "reservoir",
    seed: int = 0,
) -> CsvReport:
    """Infer column semantics from a bounded CSV sample.

    ``delimiter=None`` detects ``,``, ``;``, tab, or ``|`` from the header line.
    ``sampling="reservoir"`` (default) draws a uniform random sample of ``sample_size`` rows
    from the whole file, reproducibly for a given ``seed``, and keeps them in file order.
    ``sampling="head"`` reads only the first ``sample_size`` rows, which is faster but biased
    when the file is sorted.
    """
    from . import infer_table

    if sample_size <= 0:
        raise ValueError("sample_size must be greater than zero.")
    if sampling not in ("reservoir", "head"):
        raise ValueError("sampling must be 'reservoir' or 'head'.")
    if delimiter is not None and len(delimiter) != 1:
        raise ValueError("delimiter must be a single character.")

    source_path = Path(path)
    try:
        with source_path.open(encoding=encoding, newline="") as source:
            used_delimiter = delimiter or detect_delimiter(source.readline())
            source.seek(0)
            reader = csv.reader(source, delimiter=used_delimiter)
            headers = next(reader, None)
            if not headers or any(not header.strip() for header in headers):
                raise ValueError("CSV input must include a non-empty header row.")
            width = len(headers)
            picked: list[tuple[int, list[str]]] = []
            generator = random.Random(seed)
            malformed_flags: dict[int, bool] = {}
            rows_read = 0
            for record in reader:
                if not record:
                    continue
                if sampling == "head" and len(picked) == sample_size:
                    break
                index = rows_read
                rows_read += 1
                if sampling == "head":
                    slot: int | None = len(picked)
                elif len(picked) < sample_size:
                    slot = len(picked)
                else:
                    candidate = generator.randint(0, index)
                    slot = candidate if candidate < sample_size else None
                if slot is None:
                    continue
                entry = (index, (record + [""] * width)[:width])
                malformed_flags[index] = len(record) != width
                if slot == len(picked):
                    picked.append(entry)
                else:
                    malformed_flags.pop(picked[slot][0], None)
                    picked[slot] = entry
            picked.sort(key=lambda item: item[0])
            rows = [record for _, record in picked]
            malformed_rows = sum(malformed_flags.values())
    except UnicodeDecodeError as error:
        raise ValueError(
            f"Could not decode {source_path} as '{encoding}'. "
            "Pass the file's real encoding (for example 'latin-1' or 'cp1252')."
        ) from error

    warnings = _duplicate_header_warnings(headers)
    if malformed_rows:
        warnings.append(
            f"{malformed_rows} sampled row(s) had a different number of fields than the header; "
            "missing fields were treated as empty and extra fields were ignored."
        )

    columns_input = []
    for position, header in enumerate(headers):
        values = [row[position] for row in rows if row[position] != ""]
        columns_input.append(
            {
                "column_name": header,
                "profile": profile_values(values),
                "detected_pattern": detect_column_pattern(values),
            }
        )

    with temporary_profile(profile_name, vocabulary_paths):
        inferred = infer_table(columns_input)
    columns: list[CsvColumnResult] = [
        {**result, "column_name": header, "column_index": index}
        for index, (result, header) in enumerate(zip(inferred, headers, strict=True))
    ]
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
        "sampling": sampling,
        "rows_read": rows_read,
        "rows_sampled": len(rows),
        "rows_malformed": malformed_rows,
        "warnings": warnings,
        "columns": columns,
        "summary": summary,
    }
