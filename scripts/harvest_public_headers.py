"""Collect column names from public open-data catalogs (run manually; needs internet).

Writes ``socrata.json`` and ``ckan.json`` into the output directory. Used to find frequent
column-name words that the vocabulary does not know and to build the public benchmarks. Only
column names and declared types are kept, never data rows.

    python scripts/harvest_public_headers.py ./harvest
"""

from __future__ import annotations

import concurrent.futures as futures
import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

HEADERS = {"User-Agent": "colsemantics-vocabulary-research"}
CKAN_PORTALS = (
    "dados.pbh.gov.br",
    "dados.mg.gov.br",
    "dados.recife.pe.gov.br",
    "dados.rs.gov.br",
    "dados.es.gov.br",
    "dados.prefeitura.sp.gov.br",
    "dadosabertos.aneel.gov.br",
)


def fetch(url: str, byte_range: str | None = None) -> bytes:
    headers = dict(HEADERS)
    if byte_range:
        headers["Range"] = byte_range
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=40).read()


def harvest_socrata(pages: int = 45) -> list[dict[str, object]]:
    datasets: list[dict[str, object]] = []
    for page in range(pages):
        url = (
            "https://api.us.socrata.com/api/catalog/v1?only=datasets&limit=100"
            f"&offset={page * 100}&order=page_views_total"
        )
        try:
            results = json.loads(fetch(url)).get("results", [])
        except OSError:
            time.sleep(3)
            continue
        for item in results:
            resource = item["resource"]
            columns = zip(
                resource.get("columns_name", []),
                resource.get("columns_field_name", []),
                resource.get("columns_datatype", []),
                strict=False,
            )
            datasets.append(
                {"id": resource["id"], "domain": item["metadata"]["domain"], "cols": list(columns)}
            )
        time.sleep(0.3)
    return datasets


def ckan_resources(portal: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for start in range(0, 600, 100):
        url = f"https://{portal}/api/3/action/package_search?rows=100&start={start}"
        try:
            packages = json.loads(fetch(url))["result"]["results"]
        except (OSError, KeyError, ValueError):
            break
        for package in packages:
            for resource in package.get("resources", []):
                if (resource.get("format") or "").upper() == "CSV" and resource.get("url"):
                    found.append((portal, resource["url"]))
    return found[:120]


def csv_header(item: tuple[str, str]) -> dict[str, object] | None:
    portal, url = item
    try:
        raw = fetch(url, "bytes=0-6143")
    except OSError:
        return None
    text = raw.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    if not lines:
        return None
    delimiter = max(
        (",", ";", "\t", "|"), key=lambda d: len(next(csv.reader([lines[0]], delimiter=d)))
    )
    columns = [c.strip() for c in next(csv.reader([lines[0]], delimiter=delimiter)) if c.strip()]
    if len(columns) < 2 or any(len(c) > 60 for c in columns):
        return None
    return {"portal": portal, "url": url, "cols": columns}


def main(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "socrata.json").write_text(json.dumps(harvest_socrata()), encoding="utf-8")
    resources = [item for portal in CKAN_PORTALS for item in ckan_resources(portal)]
    with futures.ThreadPoolExecutor(8) as pool:
        headers = [header for header in pool.map(csv_header, resources) if header]
    (output / "ckan.json").write_text(json.dumps(headers, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "harvest"))
