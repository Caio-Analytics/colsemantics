# Security Policy

## Supported versions

Only the latest release on PyPI receives fixes.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/Caio-Analytics/colsemantics/security/advisories/new). Do not open a public issue. Expect an acknowledgement within a few days.

## Scope notes

colsemantics reads column names and sampled values. Its `sensitivity` field is a heuristic recommendation, not a guarantee that data is free of personal information. Treat misclassification of sensitive columns as a bug and report it with synthetic examples.
