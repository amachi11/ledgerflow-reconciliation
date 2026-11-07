"""CSV parsing and explicit input validation; all records stay local."""
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerflow.models import Transaction

REQUIRED_COLUMNS = ("id", "date", "amount", "description")


class DataError(ValueError):
    """Raised for malformed user-supplied CSV data."""


def _money(raw: str, row_number: int) -> Decimal:
    try:
        value = Decimal(raw.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise DataError(f"Row {row_number}: invalid amount {raw!r}") from exc
    if not value.is_finite() or value.as_tuple().exponent < -2:
        raise DataError(f"Row {row_number}: amount must be a finite number with at most 2 decimal places")
    return value.quantize(Decimal("0.01"))


def read_transactions(file_path: str | Path) -> list[Transaction]:
    """Load the standard schema, raising descriptive errors on invalid rows."""
    path = Path(file_path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise DataError("Missing CSV header")
        missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
        if missing:
            raise DataError(f"Missing required columns: {', '.join(sorted(missing))}")

        output: list[Transaction] = []
        seen: set[str] = set()
        for line_no, row in enumerate(reader, start=2):
            if None in row:
                raise DataError(f"Row {line_no}: more columns than the header")
            transaction_id = (row.get("id") or "").strip()
            description = (row.get("description") or "").strip()
            if not transaction_id or not description:
                raise DataError(f"Row {line_no}: id and description cannot be blank")
            if transaction_id in seen:
                raise DataError(f"Row {line_no}: duplicate transaction id {transaction_id!r}")
            seen.add(transaction_id)
            try:
                booked_on = date.fromisoformat((row.get("date") or "").strip())
            except ValueError as exc:
                raise DataError(f"Row {line_no}: date must be YYYY-MM-DD") from exc
            output.append(Transaction(
                transaction_id=transaction_id,
                booked_on=booked_on,
                amount=_money(row.get("amount") or "", line_no),
                description=description,
                reference=(row.get("reference") or "").strip(),
            ))
    return output
