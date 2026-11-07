"""Command-line interface for local, offline reconciliation."""
import argparse
import sys

from ledgerflow.csvio import DataError, read_transactions
from ledgerflow.matching import MatchOptions, reconcile
from ledgerflow.reporting import write_json, write_matches_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare a bank statement against an internal ledger without uploading data."
    )
    parser.add_argument("bank", help="Bank CSV file: id,date,amount,description,reference")
    parser.add_argument("ledger", help="Internal ledger CSV with the same schema")
    parser.add_argument("--max-days", type=int, default=3, metavar="N",
                        help="Maximum date difference for description-based matches (default: 3)")
    parser.add_argument("--min-similarity", type=float, default=0.25, metavar="X",
                        help="Minimum token overlap 0..1 (default: 0.25)")
    parser.add_argument("--json-out", help="Write a machine-readable audit report")
    parser.add_argument("--matches-out", help="Write a matched-pairs CSV")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bank = read_transactions(args.bank)
        ledger = read_transactions(args.ledger)
        options = MatchOptions(args.max_days, args.min_similarity)
        result = reconcile(bank, ledger, options)
        if args.json_out:
            write_json(result, args.json_out)
        if args.matches_out:
            write_matches_csv(result, args.matches_out)
    except (DataError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Bank records:       {len(bank)}")
    print(f"Ledger records:     {len(ledger)}")
    for key, value in result.summary().items():
        print(f"{key.replace('_', ' ').title():19}{value}")
    if result.ambiguous_bank:
        print("Review ambiguous bank IDs: " + ", ".join(result.ambiguous_bank))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
