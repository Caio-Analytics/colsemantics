import argparse
import csv
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .benchmark import evaluate_cases, load_cases
from .csv_inference import infer_csv


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="colsemantics")
    commands = parser.add_subparsers(dest="command", required=True)
    infer = commands.add_parser("infer", help="infer semantic labels from a CSV file")
    infer.add_argument("input", help="CSV file to analyze")
    infer.add_argument("--profile", default="pt-BR", help="embedded vocabulary profile")
    infer.add_argument("--sample", type=int, default=10000, help="maximum rows to sample")
    infer.add_argument("--vocabulary", help="comma-separated YAML vocabulary paths")
    infer.add_argument("--encoding", default="utf-8", help="CSV input encoding")
    infer.add_argument("--output", required=True, help="JSON report path")
    benchmark = commands.add_parser("benchmark", help="evaluate JSON benchmark cases")
    benchmark.add_argument("cases", help="JSON benchmark fixture path")
    benchmark.add_argument("--output", required=True, help="JSON report path")
    return parser


def _write_json(payload: object, output: str) -> None:
    with Path(output).open("w", encoding="utf-8") as destination:
        json.dump(payload, destination, ensure_ascii=False, indent=2)
        destination.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
    except SystemExit as error:
        return error.code if isinstance(error.code, int) else 2

    try:
        if args.command == "infer":
            report = infer_csv(
                args.input,
                sample_size=args.sample,
                profile_name=args.profile,
                vocabulary_paths=args.vocabulary,
                encoding=args.encoding,
            )
            _write_json(report, args.output)
            return 0
        if args.command == "benchmark":
            _write_json(evaluate_cases(load_cases(args.cases)), args.output)
            return 0
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
