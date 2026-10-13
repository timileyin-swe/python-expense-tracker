# Development log

## 2026-10-13 — Lock text-length boundaries with tests

### Completed

- Added `test_category_length_boundaries()` for an accepted 50-character
  category and a rejected 51-character category.
- Added `test_note_length_boundaries()` for an accepted 500-character note and a
  rejected 501-character note.
- Verified that surrounding whitespace is trimmed before length checks and that
  categories are normalized to lowercase.
- Verified that rejected values do not create partial rows.
- Replaced the quick-start sample with a realistic, disposable practice-database
  workflow and updated the study guide and development plan to Version 1.2.
- Kept production functions unchanged because the existing validation behavior
  already satisfied the documented contract.

### Tested

- `python -m compileall -q expense_tracker tests`: completed successfully.
- Targeted boundary run: 2 tests passed.
- `python -m unittest discover -s tests -v`: 14 tests passed.
- Ran the documented groceries/data workflow end to end: two expenses were added,
  `show 1` returned the expected row, the October summary totaled NGN 6,500.00,
  and CSV assertions confirmed two rows with exact decimal amounts.

### Pending

- An `update` command with explicit field selection and validation.
- Atomic CSV import.
- Any HTTP API, PostgreSQL integration, authentication, cloud deployment,
  observability, or multi-user support.

### Blocked

- Nothing for this milestone.

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
