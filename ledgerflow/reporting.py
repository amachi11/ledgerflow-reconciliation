"""Stable audit reports in JSON and CSV formats."""
import csv
import json
from pathlib import Path

from ledgerflow.models import ReconciliationResult


def report_dict(result: ReconciliationResult) -> dict:
    return {
        "summary": result.summary(),
        "matches": [
            {"bank_id": m.bank_id, "ledger_id": m.ledger_id, "method": m.method,
             "score": m.score, "days_apart": m.days_apart}
            for m in result.matches
        ],
        "unmatched_bank": list(result.unmatched_bank),
        "unmatched_ledger": list(result.unmatched_ledger),
        "ambiguous_bank": list(result.ambiguous_bank),
    }


def write_json(result: ReconciliationResult, file_path: str | Path) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report_dict(result), indent=2) + "\n", encoding="utf-8")


def write_matches_csv(result: ReconciliationResult, file_path: str | Path) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["bank_id", "ledger_id", "method", "score", "days_apart"])
        for m in result.matches:
            writer.writerow([m.bank_id, m.ledger_id, m.method, m.score, m.days_apart])
