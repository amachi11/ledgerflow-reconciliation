import unittest
from datetime import date
from decimal import Decimal
from ledgerflow.matching import MatchOptions, reconcile
from ledgerflow.models import Transaction


def tx(identifier, amount, description, reference="", day=10):
    return Transaction(identifier, date(2026, 1, day), Decimal(amount), description, reference)


class MatchingTests(unittest.TestCase):
    def test_reference_match_ignores_date_tolerance(self):
        r = reconcile([tx("B1", "12.00", "Different", "x-1", day=1)],
                      [tx("L1", "12.00", "Other", "X1", day=20)])
        self.assertEqual(r.matches[0].method, "reference")
        self.assertEqual(r.matches[0].days_apart, 19)

    def test_amount_must_match(self):
        r = reconcile([tx("B1", "12.00", "Office supplies", "R1")],
                      [tx("L1", "13.00", "Office supplies", "R1")])
        self.assertEqual(r.summary()["matched"], 0)

    def test_description_fallback_match(self):
        r = reconcile([tx("B1", "20.00", "Monthly hosting service")],
                      [tx("L1", "20.00", "Service hosting monthly", day=12)])
        self.assertEqual(r.matches[0].method, "description-date")

    def test_ambiguous_bank_record_not_assigned(self):
        bank = [tx("B1", "5.00", "Office supplies")]
        ledger = [tx("L1", "5.00", "Office supplies"), tx("L2", "5.00", "Office supplies")]
        r = reconcile(bank, ledger)
        self.assertEqual(r.ambiguous_bank, ("B1",))
        self.assertEqual(len(r.matches), 0)

    def test_identical_references_on_ledger_flagged(self):
        bank = [tx("B1", "5.00", "Office supplies", "R3")]
        ledger = [tx("L1", "5.00", "Office supplies", "R3"), tx("L2", "5.00", "Office supplies", "R3")]
        r = reconcile(bank, ledger)
        self.assertEqual(r.ambiguous_bank, ("B1",))

    def test_repeated_bank_reference_is_ambiguous(self):
        bank = [
            tx("B1", "12.00", "Invoice payment", "INV-9"),
            tx("B2", "12.00", "Invoice payment", "inv9"),
        ]
        ledger = [tx("L1", "12.00", "Invoice payment", "INV9")]
        result = reconcile(bank, ledger)
        self.assertEqual(result.matches, ())
        self.assertEqual(result.ambiguous_bank, ("B1", "B2"))
        self.assertEqual(result.unmatched_ledger, ("L1",))

    def test_same_reference_with_different_amounts_is_not_ambiguous(self):
        bank = [tx("B1", "12.00", "Invoice", "INV-9"),
                tx("B2", "15.00", "Invoice", "INV-9")]
        ledger = [tx("L1", "15.00", "Invoice", "INV9"),
                  tx("L2", "12.00", "Invoice", "INV9")]
        result = reconcile(bank, ledger)
        self.assertEqual({(m.bank_id, m.ledger_id) for m in result.matches},
                         {("B1", "L2"), ("B2", "L1")})
        self.assertEqual(result.ambiguous_bank, ())

    def test_same_ledger_cannot_be_used_twice(self):
        bank = [tx("B1", "4.00", "Coffee shop"), tx("B2", "4.00", "Coffee shop")]
        ledger = [tx("L1", "4.00", "Coffee shop")]
        r = reconcile(bank, ledger)
        self.assertEqual(len(r.matches), 1)
        self.assertEqual(len(r.unmatched_bank), 1)

    def test_date_tolerance(self):
        r = reconcile([tx("B1", "7.00", "Office supplies", day=10)],
                      [tx("L1", "7.00", "Office supplies", day=15)], MatchOptions(max_days_apart=2))
        self.assertEqual(len(r.matches), 0)

    def test_invalid_options(self):
        with self.assertRaises(ValueError):
            MatchOptions(max_days_apart=-1)
        with self.assertRaises(ValueError):
            MatchOptions(min_description_similarity=1.5)
