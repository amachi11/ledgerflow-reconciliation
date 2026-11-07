"""Explainable two-stage, one-to-one transaction matching."""
from dataclasses import dataclass

from ledgerflow.models import Match, ReconciliationResult, Transaction
from ledgerflow.normalize import description_similarity, normalize_reference


@dataclass(frozen=True)
class MatchOptions:
    max_days_apart: int = 3
    min_description_similarity: float = 0.25

    def __post_init__(self) -> None:
        if self.max_days_apart < 0:
            raise ValueError("max_days_apart must be nonnegative")
        if not 0 <= self.min_description_similarity <= 1:
            raise ValueError("min_description_similarity must be between 0 and 1")


def reconcile(
    bank: list[Transaction],
    ledger: list[Transaction],
    options: MatchOptions | None = None,
) -> ReconciliationResult:
    """Reconcile debits/credits using equal signed amounts and independent identifiers.

    Stage 1: equal amount + normalized reference, requiring an unambiguous pair.
    Stage 2: equal amount + date tolerance + description token overlap.
    A tied best candidate in stage 2 is flagged for manual review.
    """
    options = options or MatchOptions()
    matches: list[Match] = []
    bank_remaining = {tx.transaction_id: tx for tx in bank}
    ledger_remaining = {tx.transaction_id: tx for tx in ledger}
    if len(bank_remaining) != len(bank) or len(ledger_remaining) != len(ledger):
        raise ValueError("Transaction IDs must be unique within each input")

    # Never guess between duplicate references; preserve ambiguous rows for review.
    ambiguous: set[str] = set()
    for b in sorted(bank, key=lambda tx: tx.transaction_id):
        if b.transaction_id not in bank_remaining:
            continue
        reference = normalize_reference(b.reference)
        if not reference:
            continue
        candidates = [l for l in ledger_remaining.values()
                      if l.amount == b.amount and normalize_reference(l.reference) == reference]
        if len(candidates) == 1:
            l = candidates[0]
            matches.append(Match(b.transaction_id, l.transaction_id, "reference", 100,
                                 abs((b.booked_on - l.booked_on).days)))
            del bank_remaining[b.transaction_id]
            del ledger_remaining[l.transaction_id]
        elif len(candidates) > 1:
            ambiguous.add(b.transaction_id)

    # Prioritize highly similar descriptions and then closer dates. Do not commit
    # if multiple remaining ledger candidates have the same best score.
    proposals: list[tuple[int, int, str, str]] = []
    for b in bank_remaining.values():
        if b.transaction_id in ambiguous:
            continue
        scores: list[tuple[int, int, str]] = []
        for l in ledger_remaining.values():
            days = abs((b.booked_on - l.booked_on).days)
            if b.amount != l.amount or days > options.max_days_apart:
                continue
            similarity = description_similarity(b.description, l.description)
            if similarity < options.min_description_similarity:
                continue
            score = round(similarity * 100) + max(0, 20 - days * 5)
            scores.append((score, days, l.transaction_id))
        if not scores:
            continue
        scores.sort(key=lambda x: (-x[0], x[1], x[2]))
        best_score, best_days, best_id = scores[0]
        if len(scores) > 1 and scores[1][0] == best_score and scores[1][1] == best_days:
            ambiguous.add(b.transaction_id)
            continue
        proposals.append((best_score, best_days, b.transaction_id, best_id))

    for score, days, bank_id, ledger_id in sorted(proposals, key=lambda x: (-x[0], x[1], x[2], x[3])):
        if bank_id not in bank_remaining or ledger_id not in ledger_remaining:
            continue
        matches.append(Match(bank_id, ledger_id, "description-date", score, days))
        del bank_remaining[bank_id]
        del ledger_remaining[ledger_id]

    return ReconciliationResult(
        matches=tuple(sorted(matches, key=lambda m: m.bank_id)),
        unmatched_bank=tuple(sorted(set(bank_remaining) - ambiguous)),
        unmatched_ledger=tuple(sorted(ledger_remaining)),
        ambiguous_bank=tuple(sorted(ambiguous)),
    )
