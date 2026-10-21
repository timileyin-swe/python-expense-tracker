# Python Expense Tracker

A local command-line application for recording NGN expenses, finding one expense
by ID, filtering by month and category, viewing category totals, creating
consistent database backups, importing CSV files, and exporting CSV or JSON.
Built as a learning portfolio project using Python's standard library; no
external packages are required.

## Quick start

Install Python 3.10 or newer, clone this repository, and open a terminal in its
folder. On Windows, replace `python` with `py` if necessary.

```sh
python -m expense_tracker --db practice.db add 4500 groceries --date 2026-10-14 --note "Rice and vegetables"
python -m expense_tracker --db practice.db add 2000 data --date 2026-10-14 --note "Weekly mobile data"
python -m expense_tracker --db practice.db update 1 --amount 5200.50 --category household --note ""
python -m expense_tracker --db practice.db backup practice-backup.db
python -m expense_tracker --db practice.db show 1
python -m expense_tracker --db practice.db list --month 2026-10 --category household
python -m expense_tracker --db practice.db summary --month 2026-10
python -m expense_tracker --db practice.db export expenses.csv --month 2026-10
python -m expense_tracker --db practice.db export-json expenses.json --month 2026-10
python -m expense_tracker --db restored.db import expenses.csv
```

Example `show` result:

```text
#1 | 2026-10-14 | NGN 5,200.50 | household |
```

Example summary:

```text
data: NGN 2,000.00
household: NGN 5,200.50
TOTAL: NGN 7,200.50
```

Data survives application restarts in `~/.expense-tracker/expenses.db`.
Override the location with `python -m expense_tracker --db demo.db list`.
All amounts use NGN; currencies cannot be mixed.

## Design

- `argparse` turns terminal input into commands.
- Validation rejects invalid dates, nonpositive amounts, fractional kobo, and
  invalid IDs.
- Categories are trimmed, lowercased, and limited to 50 characters. Notes are
  trimmed and limited to 500 characters.
- `Decimal` converts decimal amounts to integer kobo for exact storage and sums.
- SQLite provides transactional persistence; parameterized SQL separates data
  from SQL.
- `ExpenseStore.get()` returns one row or `None`, while the CLI decides how to
  present a missing record to a user.
- `ExpenseStore.update()` validates every supplied field before one parameterized
  update and preserves fields that were not selected.
- `ExpenseStore.list()` builds optional month and category conditions from
  hard-coded SQL fragments while keeping filter values in parameters. `summary()`
  and `export()` reuse the same filtering path.
- `ExpenseStore.import_csv()` validates every row before one transaction inserts
  anything. Strict parsing rejects malformed quotes, errors identify the physical
  CSV line, and imported source IDs are ignored.
- `expense_to_dict()` maps a SQLite row to JSON-compatible fields, keeping the
  exact NGN amount as a two-decimal string. `ExpenseStore.export_json()` writes
  those records as readable UTF-8 JSON and reuses the existing filters.
- `ExpenseStore.backup()` uses SQLite's backup API to create or refresh a
  consistent snapshot, creates missing destination folders, and rejects the live
  database itself as the destination.
- `format_expense()` gives `list`, `show`, and `update` one shared output format.
- `format_expense_count()` gives import and export commands correct singular or
  plural count messages without duplicating grammar logic.
- CSV text fields are protected against common spreadsheet formula prefixes.
- Deletion validates a positive integer ID before SQL and requires explicit
  confirmation: `python -m expense_tracker delete 1 --yes`.

## Test

```sh
python -m unittest discover -s tests -v
```

The current suite contains 30 tests. It uses temporary databases and covers
persistence, exact money, invalid input, category and note length boundaries,
month/category filters and totals, single-record lookup, partial updates, rejected
updates, filtered CSV export, atomic CSV import, malformed headers, fields and
quoted syntax, singular/plural count messages, SQL-looking notes, deletion
confirmation, rejected deletion IDs, independent and refreshed database backups,
same-path backup rejection, filtered JSON export, exact JSON money strings,
Unicode preservation, and CLI commands.

## Learn the project

Read [the complete study guide](docs/STUDY_GUIDE.md), then complete its practical
exercises. [The development log](docs/DEVELOPMENT_LOG.md) separates completed,
tested, pending, and blocked work. [The next-step plan](docs/NEXT_STEPS.md) lists
future milestones without presenting them as finished features.

## Scope and limitations

This is a single-user local CLI, with no web interface, authentication, encryption,
or cloud deployment. Category filtering is an exact normalized match, not partial
or fuzzy search. CSV and JSON exports overwrite their specified output files.
JSON export writes `amount_ngn` as a string for exact decimal text, and JSON import
is not implemented. CSV import accepts only its documented headers, generates new
IDs, and does not detect duplicates. The backup command creates a full local
database snapshot; it is not automatic, encrypted, uploaded, or a per-record undo
feature. Reusing a destination refreshes that backup. Deletion has no built-in
undo, so create and verify a backup first. Do not commit personal spending records;
database, CSV, and JSON files are ignored by Git.

Development uses AI assistance. Learning and hands-on exercises are documented
separately from implementation; this repository makes no claims about production
users, independent authorship, or measured business impact.
