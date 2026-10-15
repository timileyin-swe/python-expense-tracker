# Development log

## 2026-10-15 — Atomic CSV import

### Completed

- Added `ExpenseStore.import_csv()` for the documented
  `amount_ngn,category,date,note` header and the app's exported format with an
  optional leading `id` column.
- Read and validate every row before opening the insert transaction, so an invalid
  later row cannot leave earlier rows in the database.
- Added line-specific validation errors for bad row shapes, amounts, categories,
  dates, and notes.
- Ignored source IDs and let SQLite generate fresh local IDs, preventing imported
  files from colliding with existing records.
- Accepted UTF-8 CSV files with or without a byte-order mark and added the
  `python -m expense_tracker import PATH` command.
- Updated the README, study guide, and development plan to Version 1.4.

### Tested

- `python -m compileall -q expense_tracker tests`: completed successfully.
- Four targeted import tests passed.
- `python -m unittest discover -s tests -v`: 21 tests passed.
- Verified an export-to-import round trip into a database that already had a row,
  fresh ID allocation, four-column input, CLI output, bad-header rejection, extra
  field rejection, and rollback-by-design when line 3 contained an invalid amount.
- Ran an end-to-end export/import/list/summary workflow: two records imported into
  a fresh database and the October total remained NGN 7,200.50.

### Pending

- Hands-on learner completion of the Version 1.4 exercises.
- The separate job-application API, followed later by PostgreSQL, queues, Docker,
  monitoring, an AI document assistant, and optional cloud deployment.

### Blocked

- Publishing the prepared job-application API remains blocked because the
  connected GitHub capabilities cannot create a repository and the intended
  repository does not yet exist. No unrelated repository was used as a substitute.

## 2026-10-14 — Update selected expense fields

### Completed

- Added `ExpenseStore.update()` with keyword-only optional fields for amount,
  category, date, and note.
- Preserved every omitted field and allowed `--note ""` to intentionally clear a
  note.
- Added shared `valid_expense_id()`, `normalize_category()`, and
  `normalize_note()` helpers so add, get, and update use consistent rules.
- Validated every supplied change before one parameterized SQL update.
- Returned the updated row for reuse by the CLI while returning `None` for a
  well-formed missing ID.
- Added `python -m expense_tracker update ID [OPTIONS]` and updated the README,
  study guide, and development plan to Version 1.3.

### Tested

- `python -m compileall -q expense_tracker tests`: completed successfully.
- Three targeted update tests passed.
- `python -m unittest discover -s tests -v`: 17 tests passed.
- Verified selected-field updates, preservation of an omitted date, intentional
  note clearing, rejected invalid changes, no-field errors, and missing-ID errors.
- Ran an end-to-end add/update/show/summary workflow; the stored row contained
  NGN 5,200.50, category `household`, the original date, and an empty note.

### Pending

- Atomic CSV import with line-specific validation errors.
- Any HTTP API, PostgreSQL integration, authentication, cloud deployment,
  observability, or multi-user support.

### Blocked

- Nothing for this milestone.

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
