"""Rebuild src/colsemantics/data/*.txt from public sources (run manually; needs internet).

Sources (see src/colsemantics/data/SOURCES.md for licenses):
  - IBGE localities API: Brazilian municipalities and countries.
  - IBGE census names API: most frequent Brazilian first names (top 20 per state, decade, sex).
  - SSA baby names via hadley/data-baby-names: most common US first names.
  - datasets/world-cities: US city names and country names.
Only derived word lists are stored, never the raw files.
"""

from __future__ import annotations

import collections
import concurrent.futures as futures
import csv
import io
import json
import urllib.request
from pathlib import Path

from colsemantics import normalize

DATA = Path(__file__).parents[1] / "src" / "colsemantics" / "data"
HEADERS = {"User-Agent": "colsemantics-vocabulary-build"}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(request, timeout=90).read()


def write(name: str, values: list[str]) -> None:
    unique = sorted({normalize(value) for value in values if normalize(value)})
    (DATA / name).write_text("\n".join(unique) + "\n", encoding="utf-8")
    print(f"{name}: {len(unique)} values")


# Common short forms that the official lists spell differently.
COUNTRY_ALIASES = [
    "Estados Unidos", "EUA", "USA", "United States of America", "Coreia do Sul",
    "Coreia do Norte", "Rússia", "UK", "Great Britain", "Inglaterra", "México", "Mexico",
]  # fmt: skip


def main() -> None:
    municipalities = json.loads(
        fetch("https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado")
    )
    write("br_municipalities.txt", [item["municipio-nome"] for item in municipalities])

    states = json.loads(fetch("https://servicodados.ibge.gov.br/api/v1/localidades/estados"))
    countries = json.loads(fetch("https://servicodados.ibge.gov.br/api/v1/localidades/paises"))

    cities_csv = fetch(
        "https://raw.githubusercontent.com/datasets/world-cities/main/data/world-cities.csv"
    ).decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(cities_csv)))
    write(
        "countries.txt",
        [c["nome"] for c in countries] + [r["country"] for r in rows] + COUNTRY_ALIASES,
    )
    write("us_cities.txt", [r["name"] for r in rows if r["country"] == "United States"])

    def ranking(job: tuple[int, int, str]) -> list[tuple[str, int]]:
        state, decade, sex = job
        url = (
            "https://servicodados.ibge.gov.br/api/v2/censos/nomes/ranking"
            f"?decada={decade}&sexo={sex}&localidade={state}"
        )
        try:
            payload = json.loads(fetch(url))
            return [(item["nome"], item["frequencia"]) for item in payload[0]["res"]]
        except Exception:
            return []

    jobs = [(s["id"], d, x) for s in states for d in range(1930, 2011, 10) for x in "MF"]
    frequency: collections.Counter[str] = collections.Counter()
    with futures.ThreadPoolExecutor(6) as pool:
        for result in pool.map(ranking, jobs):
            for name, count in result:
                frequency[name] += count
    write("br_first_names.txt", [name for name, _ in frequency.most_common()])

    baby_csv = fetch(
        "https://raw.githubusercontent.com/hadley/data-baby-names/master/baby-names.csv"
    ).decode("utf-8")
    us: collections.Counter[str] = collections.Counter()
    for row in csv.DictReader(io.StringIO(baby_csv)):
        us[row["name"]] += float(row["percent"])
    write("us_first_names.txt", [name for name, _ in us.most_common(1500)])


if __name__ == "__main__":
    main()
