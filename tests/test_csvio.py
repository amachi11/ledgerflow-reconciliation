import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from ledgerflow.csvio import DataError, read_transactions


class CsvTests(unittest.TestCase):
    def read(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.csv"
            path.write_text(content, encoding="utf-8")
            return read_transactions(path)

    def test_parses_valid_rows(self):
        result = self.read("id,date,amount,description,reference\nA,2026-02-01,-12.30,Sample,R1\n")
        self.assertEqual(result[0].amount, Decimal("-12.30"))
        self.assertEqual(result[0].reference, "R1")

    def test_missing_required_header(self):
        with self.assertRaisesRegex(DataError, "Missing required columns"):
            self.read("id,date,description\nA,2026-01-01,Example\n")

    def test_duplicate_id(self):
        with self.assertRaisesRegex(DataError, "duplicate transaction id"):
            self.read("id,date,amount,description\nA,2026-01-01,1.00,Example\nA,2026-01-02,2.00,Example\n")

    def test_bad_amount(self):
        with self.assertRaisesRegex(DataError, "amount must be"):
            self.read("id,date,amount,description\nA,2026-01-01,1.234,Example\n")

    def test_bad_date(self):
        with self.assertRaisesRegex(DataError, "date must be"):
            self.read("id,date,amount,description\nA,not-a-date,1.00,Example\n")
