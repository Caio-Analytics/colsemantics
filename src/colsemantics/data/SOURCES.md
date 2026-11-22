# Word lists

Only derived, normalized word lists are shipped, never the raw files. Rebuild the gazetteers with
`python scripts/build_gazetteer_data.py`.

| File | Source | License / terms |
|---|---|---|
| `br_municipalities.txt` | IBGE localities API (`servicodados.ibge.gov.br/api/v1/localidades/municipios`) | IBGE open data, attribution to IBGE |
| `countries.txt` | IBGE localities API (Portuguese names) and `datasets/world-cities` (English names) | IBGE open data; ODC Public Domain Dedication and License |
| `us_cities.txt` | `datasets/world-cities` (United States rows) | ODC Public Domain Dedication and License |
| `br_first_names.txt` | IBGE census names API: most frequent first names by state, decade, and sex | IBGE open data, attribution to IBGE |
| `us_first_names.txt` | US Social Security Administration baby names, via `hadley/data-baby-names` (top 1,500 by cumulative share) | US government work, public domain |
| `modifiers.txt` | Words seen directly before words such as `date`, `id`, `code`, `name` in column names of public open-data catalogs (Socrata discovery API for US portals; CKAN portals of Brazilian governments, excluding `dados.es.gov.br`). Used to split fused names such as `issueddate`. | Column names are facts; no data rows are copied |

The vocabulary additions in `_taxonomy.py` were chosen by reading the most frequent column-name tokens
of the same catalogs (train half of the US datasets by id hash, Brazilian portals except
`dados.es.gov.br`) and classifying them by hand. The other half and `dados.es.gov.br` are held out for
evaluation; see `benchmarks/README.md`.
