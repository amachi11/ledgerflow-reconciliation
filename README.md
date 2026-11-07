# LedgerFlow Reconciliation

A **small but real multi-module Python toolkit** for comparing bank transactions with an internal ledger. It works offline, uses Python's standard library, validates messy CSV inputs, performs explainable one-to-one matching, and exports audit-friendly reports.

> For educational use and small local workflows. This is not accounting advice or a production banking system. Review every match before making a financial decision.

## Features

- Input validation for ISO dates, currency precision, required fields and duplicate transaction IDs.
- Two-stage matching: normalized references first; description similarity and date proximity second.
- Signed amounts are preserved (`-20.00` is different from `20.00`).
- Ambiguous transactions are flagged rather than guessed.
- A deterministic CSV matched-pair export and JSON audit report.
- No external APIs, credentials, database, network calls or third-party runtime dependencies.
- Unit and CLI integration tests, using synthetic sample transactions.

## Project layout

```text
ledgerflow/
  cli.py           Command-line options and output
  csvio.py         Parsing and validation
  matching.py      Matching algorithm and options
  models.py        Transaction / match / result data types
  normalize.py     Reference and description normalization
  reporting.py     JSON and CSV audit reports
examples/          Synthetic, shareable bank and ledger records
tests/             Python unittest suite
pyproject.toml     Package metadata and CLI entry point
LICENSE            MIT open-source license
```

## Quick start (Python 3.10+)

Without installing anything:

```bash
python -m ledgerflow examples/bank.csv examples/ledger.csv
```

Generate reports:

```bash
python -m ledgerflow examples/bank.csv examples/ledger.csv \
  --max-days 3 \
  --json-out reports/audit.json \
  --matches-out reports/matches.csv
```

If installed as a package (`python -m pip install -e .`), the same arguments work with the `ledgerflow` command.

## Input CSV schema

Both inputs must have these columns:

| Column | Required | Example | Notes |
|---|---|---|---|
| `id` | Yes | `TX-001` | Unique within that file |
| `date` | Yes | `2026-01-10` | ISO date |
| `amount` | Yes | `-24.50` | Signed currency value, up to two decimals |
| `description` | Yes | `Office supplies` | Free-form description |
| `reference` | No | `INV-007` | Comparison ignores separators and case |

Only synthetic example records are committed. **Do not commit real bank exports, client data, account numbers, credentials, or confidential information.**

## Matching behavior

1. Exact signed amount + normalized reference has priority, even if dates differ.
2. Remaining transactions can match by signed amount, nearby date (default: up to 3 days), and token overlap in their descriptions.
3. Equal top candidates for a bank record are held for review rather than assigned.
4. Results list matched pairs, unmatched IDs on both sides, and ambiguous bank IDs.

This rule-based method is deliberately understandable rather than claiming that every match is correct. In particular, when multiple bank records compete for one ledger transaction, one may be left unmatched and should be reviewed manually. The tool does not infer a match based only on an equal amount.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Contributing

Issue reports and pull requests are welcome. Please add a small automated test for changes to matching or CSV validation, keep examples synthetic, and explain behavior changes in plain language.

## License

MIT. See [LICENSE](LICENSE).
