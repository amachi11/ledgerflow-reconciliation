import csv
import json
import tempfile
import unittest
from pathlib import Path
from ledgerflow.cli import main
from ledgerflow.csvio import DataError

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_example_files_and_report_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "report.json"
            csv_path = Path(tmp) / "matches.csv"
            status = main([str(ROOT / "examples/bank.csv"), str(ROOT / "examples/ledger.csv"),
                           "--json-out", str(json_path), "--matches-out", str(csv_path)])
            self.assertEqual(status, 0)
            data = json.loads(json_path.read_text())
            self.assertEqual(data["summary"]["matched"], 3)
            self.assertEqual(data["summary"]["unmatched_bank"], 1)
            self.assertEqual(data["summary"]["unmatched_ledger"], 1)
            with csv_path.open(newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 3)

    def test_missing_file_returns_error_code(self):
        self.assertEqual(main(["missing-bank-file.csv", "missing-ledger-file.csv"]), 2)
