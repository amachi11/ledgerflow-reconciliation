"""Immutable domain models used by parsing, matching, and reporting."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    booked_on: date
    amount: Decimal
    description: str
    reference: str = ""


@dataclass(frozen=True)
class Match:
    bank_id: str
    ledger_id: str
    method: str
    score: int
    days_apart: int


@dataclass(frozen=True)
class ReconciliationResult:
    matches: tuple[Match, ...] = ()
    unmatched_bank: tuple[str, ...] = ()
    unmatched_ledger: tuple[str, ...] = ()
    ambiguous_bank: tuple[str, ...] = ()

    def summary(self) -> dict[str, int]:
        return {
            "matched": len(self.matches),
            "unmatched_bank": len(self.unmatched_bank),
            "unmatched_ledger": len(self.unmatched_ledger),
            "ambiguous_bank": len(self.ambiguous_bank),
        }
