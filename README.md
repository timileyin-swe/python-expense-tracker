# Python Expense Tracker

A local command-line application for recording NGN expenses, filtering by month,
viewing category totals, and exporting CSV files. Built as a learning portfolio
project using Python's standard library; no external packages are required.

## Quick start

Install Python 3.10 or newer, clone this repository, and open a terminal in its folder.
On Windows, replace `python` with `py` if necessary.

```sh
python -m expense_tracker add 1500 food --date 2026-10-12 --note "Lunch"
python -m expense_tracker add 800 transport --date 2026-10-12
python -m expense_tracker list
python -m expense_tracker summary --month 2026-10
python -m expense_tracker export expenses.csv --month 2026-10
```

Example summary:

```text
food: NGN 1,500.00
transport: NGN 800.00
TOTAL: NGN 2,300.00
```

Data survives application restarts in `~/.expense-tracker/expenses.db`.
Override the location with `python -m expense_tracker --db demo.db list`.
All amounts use NGN; currencies cannot be mixed.

## Design

- `argparse` turns terminal input into commands.
- Validation rejects invalid dates, nonpositive amounts, and fractional kobo.
- `Decimal` converts decimal amounts to integer kobo for exact storage and sums.
- SQLite provides transactional persistence; parameterized SQL separates data from SQL.
- CSV text fields are protected against common spreadsheet formula prefixes.
- Deletion requires explicit confirmation: `python -m expense_tracker delete 1 --yes`.

## Test

```sh
python -m unittest discover -s tests -v
```

Tests use temporary databases and cover persistence, exact money, invalid input,
monthly totals, export, SQL-looking notes, deletion confirmation, and CLI commands.

## Learn the project

Read [the complete study guide](docs/STUDY_GUIDE.md), then run its exercises.
[The next-step plan](docs/NEXT_STEPS.md) tracks future work.

## Scope and limitations

This is a single-user local CLI, with no web interface, authentication, encryption,
or cloud deployment. CSV export overwrites the specified output file. Back up the
SQLite file while the application is closed. Deletion has no undo. Do not commit
personal spending records; database and CSV files are ignored by Git.

Development uses AI assistance. Learning and hands-on exercises are documented
separately from implementation; this repository makes no claims about production
users, independent authorship, or measured business impact.
