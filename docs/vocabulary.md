# Custom vocabularies and data sources

## YAML extensions

Pass one or more comma-separated YAML files to `load_vocabularies`, `temporary_vocabulary`,
`temporary_profile`, `infer_csv(vocabulary_paths=...)`, or `colsemantics infer --vocabulary`.

```yaml
strong_categories:          # matched exactly against name tokens (role axis)
  Project domain:
    - workstream
fuzzy_categories:           # matched approximately (domain axis)
  Real Estate / Property:
    - lease
gazetteers:                 # value lists matched against sampled values
  - name: fruit
    values: [apple, pear, plum]
    category: Product / Item
    axis: domain            # role or domain
    minimum_coverage: 0.8   # optional, share of values that must match
    weight: 0.8             # optional
    max_distinct: 100       # optional
column_overrides:           # exact column name -> category, always conclusive
  cost_bucket: Finance / Cost
```

Extensions are scoped with `ContextVar`: concurrent analyses never share vocabulary changes.
Invalid files raise `ValueError` with the file and section.

`export_overrides_template(report, "overrides.yaml")` turns a reviewed report into
`column_overrides`, so corrections can be fed back.

## Where the built-in vocabulary comes from

Hand-written terms plus words learned from the column names of about 4,500 US open datasets
(Socrata catalog) and 500 Brazilian CKAN resources, and word lists from IBGE, the US Social
Security Administration, and `datasets/world-cities`. Only derived word lists are shipped. Sources,
licenses, and the rebuild scripts are listed in
[`src/colsemantics/data/SOURCES.md`](../src/colsemantics/data/SOURCES.md).
