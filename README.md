# Python Expense Tracker

A local command-line application for recording NGN expenses, finding one expense
by ID, filtering by month, viewing category totals, and exporting CSV files. Built
as a learning portfolio project using Python's standard library; no external
packages are required.

## Quick start

Install Python 3.10 or newer, clone this repository, and open a terminal in its
folder. On Windows, replace `python` with `py` if necessary.

```sh
python -m expense_tracker --db practice.db add 4500 groceries --date 2026-10-13 --note "Rice and vegetables"
python -m expense_tracker --db practice.db add 2000 data --date 2026-10-13 --note "Weekly mobile data"
python -m expense_tracker --db practice.db show 1
python -m expense_tracker --db practice.db list
python -m expense_tracker --db practice.db summary --month 2026-10
python -m expense_tracker --db practice.db export expenses.csv --month 2026-10
```

Example `show` result:

```text
#1 | 2026-10-13 | NGN 4,500.00 | groceries | Rice and vegetables
```

Example summary:

```text
data: NGN 2,000.00
groceries: NGN 4,500.00
TOTAL: NGN 6,500.00
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
- `format_expense()` gives the `list` and `show` commands one shared output format.
- CSV text fields are protected against common spreadsheet formula prefixes.
- Deletion requires explicit confirmation: `python -m expense_tracker delete 1 --yes`.

## Test

```sh
python -m unittest discover -s tests -v
```

The current suite contains 14 tests. It uses temporary databases and covers
persistence, exact money, invalid input, category and note length boundaries,
monthly totals, single-record lookup, CSV export, SQL-looking notes, deletion
confirmation, and CLI commands.

## Learn the project

Read [the complete study guide](docs/STUDY_GUIDE.md), then complete its practical
exercises. [The development log](docs/DEVELOPMENT_LOG.md) separates completed,
tested, pending, and blocked work. [The next-step plan](docs/NEXT_STEPS.md) lists
future milestones without presenting them as finished features.

## Scope and limitations

This is a single-user local CLI, with no web interface, authentication, encryption,
or cloud deployment. CSV export overwrites the specified output file. Back up the
SQLite file while the application is closed. Deletion has no undo. Do not commit
personal spending records; database and CSV files are ignored by Git.

Development uses AI assistance. Learning and hands-on exercises are documented
separately from implementation; this repository makes no claims about production
users, independent authorship, or measured business impact.
