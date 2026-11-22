"""Classify the columns of the sample CSV files and print a short report.

python examples/quickstart.py
"""

from pathlib import Path

from colsemantics import infer_column, infer_csv

HERE = Path(__file__).parent


def print_report(path: Path) -> None:
    report = infer_csv(path)
    print(
        f"\n{path.name}  (delimiter {report['source']['delimiter']!r}, {report['rows_sampled']} rows)"
    )
    print(f"{'column':<15} {'semantic':<26} {'sensitivity':<15} pattern")
    for column in report["columns"]:
        sensitivity = column["sensitivity"]
        pattern = column["pattern"]
        found = f"{pattern['locale'] or '-'} {pattern['type']}" if pattern else ""
        print(
            f"{column['column_name']:<15} {column['semantic']:<26} "
            f"{sensitivity['level'] + '/' + sensitivity['action']:<15} {found}"
        )


if __name__ == "__main__":
    print_report(HERE / "customers_br.csv")
    print_report(HERE / "customers_us.csv")
    print("\nNames only, no values:")
    for name in ("cd_dpto_lot", "SUPPLIER_CONTACT_CODE", "f27"):
        print(f"  {name:<22} -> {infer_column(name)['semantic']}")
