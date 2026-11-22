"""Fetch a few sample values per column from public Socrata datasets (run manually).

Reads ``socrata.json`` written by ``harvest_public_headers.py`` and the (dataset id, field)
pairs you want values for, and writes ``values.json`` mapping dataset id to field to a short
list of values. Only a handful of rows per dataset are requested.

    python scripts/fetch_public_values.py harvest/socrata.json wanted.json harvest/values.json

``wanted.json`` is a list of ``[dataset_id, field_name]`` pairs.
"""

from __future__ import annotations

import collections
import concurrent.futures as futures
import csv
import io
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def fetch_columns(domain: str, dataset: str, fields: list[str]) -> dict[str, list[str]] | None:
    select = urllib.parse.quote(",".join(sorted(set(fields))))
    url = f"https://{domain}/resource/{dataset}.csv?$limit=30&$select={select}"
    request = urllib.request.Request(
        url, headers={"User-Agent": "colsemantics-vocabulary-research"}
    )
    try:
        raw = urllib.request.urlopen(request, timeout=45).read().decode("utf-8", "replace")
    except OSError:
        return None
    columns: dict[str, list[str]] = collections.defaultdict(list)
    for row in csv.DictReader(io.StringIO(raw)):
        for key, value in row.items():
            if key and value:
                columns[key].append(value)
    return dict(columns)


def main(catalog: Path, wanted: Path, output: Path) -> None:
    domains = {item["id"]: item["domain"] for item in json.loads(catalog.read_text("utf-8"))}
    fields: dict[str, list[str]] = collections.defaultdict(list)
    for dataset, field in json.loads(wanted.read_text("utf-8")):
        fields[dataset].append(field)

    def job(dataset: str) -> tuple[str, dict[str, list[str]] | None]:
        return dataset, fetch_columns(domains[dataset], dataset, fields[dataset])

    with futures.ThreadPoolExecutor(8) as pool:
        results = dict(pool.map(job, fields))
    output.write_text(json.dumps(results), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
