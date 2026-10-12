# Development log

## 2026-10-12 — Show one expense by ID

### Completed

- Added `ExpenseStore.get(expense_id)` to retrieve one persisted expense.
- Validated that direct callers provide a positive integer ID; booleans are
  rejected even though `bool` is an `int` subclass in Python.
- Added `python -m expense_tracker show ID`.
- Added `format_expense(row)` so `show` and `list` cannot drift into two different
  display formats.
- Updated the README, study guide, and next-step plan.

### Tested

- `python -m unittest discover -s tests -v`: 12 tests passed.
- Verified add, show, list, monthly summary, and CSV export with an isolated
  temporary SQLite database.
- Verified that `show 999` for a missing record prints `Expense ID not found.` and
  exits with status 2.
- Verified exported records preserved exact amounts and expected fields.

### Pending

- Boundary tests for maximum category and note lengths.
- An update command with explicit field selection and validation.
- Atomic CSV import.
- Any HTTP API, PostgreSQL integration, authentication, cloud deployment,
  observability, or multi-user support.

### Blocked

- Nothing for this milestone.

Passing tests document checked behavior, not production readiness. Development
used AI assistance; practical mastery still requires the exercises in the study
guide.
