# Development log

## 2026-10-21 — Export filtered expenses as JSON

### Completed

- Added `expense_to_dict(row)` to map internal SQLite column names and integer
  kobo into a JSON-compatible public record.
- Represented `amount_ngn` as a two-decimal string rather than a binary
  floating-point number, preserving the same exact money contract as CSV export.
- Added `ExpenseStore.export_json(path, month=None, category=None)`, which reuses
  `list()` so unfiltered, month-only, category-only, and combined selections follow
  the existing validated query path.
- Wrote one indented UTF-8 JSON array with `ensure_ascii=False` and a final newline
  so Unicode notes remain readable and common command-line tools handle the file
  cleanly.
- Added `export-json PATH` with `--month` and `--category` options, and reused the
  existing singular/plural count formatter.
- Ignored generated `*.json` files and updated the README, study guide, and
  development plan to Version 1.7.

### Tested

- `python -m compileall -q expense_tracker tests`: completed successfully.
- Two focused storage and CLI JSON-export tests passed.
- `python -m unittest discover -s tests -v`: 30 tests passed.
- Verified exact `"12.50"` and `"1500.25"` money strings, integer IDs, documented
  field names, combined month/category filtering, a trailing newline, and direct
  parsing with `json.loads()`.
- Verified `Café` and the naira symbol remain literal UTF-8 text in the file.
- Rehearsed the real CLI with food and data expenses: the filtered command
  reported `Exported 1 expense to JSON.` and `python -m json.tool` accepted the
  generated document.

### Pending

- Hands-on learner completion of the Version 1.7 dictionary/JSON exercise.
- Continue the separate job-application API after functions, modules, exceptions,
  serialization, and resource cleanup have been demonstrated through practical
  Python work.
- Later progression to PostgreSQL, queues, Docker, monitoring, an AI document
  assistant, and optional cloud deployment.

### Blocked

- Publishing the prepared job-application API remains blocked: the intended
  repository still does not exist and repository creation is unavailable through
  the connected GitHub actions. The starter bundle remains preserved separately;
  no unrelated repository was modified.

## 2026-10-20 — Add consistent database backups

### Completed

- Added `ExpenseStore.backup(path)`, which creates missing parent folders and
  uses SQLite's connection backup API to create or refresh a consistent database
  snapshot.
- Rejected a destination that resolves to the live database path, including an
  equivalent path containing `.`, before opening the destination connection.
- Closed the destination connection in a `finally` block while continuing to use
  the store's existing context manager for source connection cleanup.
- Added `python -m expense_tracker --db SOURCE backup DESTINATION` and kept output
  formatting in the command-line layer.
- Updated the README, study guide, and development plan to Version 1.6 with
  beginner-readable coverage of methods, `Path` objects, snapshots, validation,
  transactions, and resource cleanup.

### Tested

- `python -m compileall -q expense_tracker tests`: completed successfully.
- Two focused storage and CLI backup tests passed.
- `python -m unittest discover -s tests -v`: 28 tests passed.
- Proved that a new nested backup folder is created, a snapshot can be reopened,
  later source updates do not change that snapshot, and rerunning backup refreshes
  the destination with current source state.
- Proved an equivalent source path is rejected and the CLI prints the destination.
- Rehearsed add/backup/update/delete end to end: the live database became empty
  while the backup still returned expense 1 with its original NGN 1,500.00 amount
  and note.

### Pending

- Hands-on learner completion of the Version 1.6 backup exercise.
- Continue the separate job-application API after functions, modules, exceptions,
  and resource cleanup have been demonstrated through practical Python work.
- Later progression to PostgreSQL, queues, Docker, monitoring, an AI document
  assistant, and optional cloud deployment.

### Blocked

- Publishing the prepared job-application API remains blocked: the intended
  repository still does not exist and repository creation is unavailable through
  the connected GitHub actions. The starter bundle remains preserved separately;
  no unrelated repository was modified.

## 2026-10-19 — Correct singular and plural count messages

### Completed

- Added the pure `format_expense_count(count)` CLI helper so an exact count of one
  uses `expense`, while zero and every other count use `expenses`.
- Replaced duplicated import and export count wording with the shared helper.
- Kept persistence methods unchanged: they still return integers, while the
  command-line presentation layer owns English grammar.
- Corrected the README practice workflow so its unfiltered summary matches the
  documented NGN 7,200.50 example.
- Updated the README, study guide, and development plan to Version 1.5.1 with
  beginner-readable coverage of functions, parameters, local variables,
  conditional expressions, return values, and pure functions.

### Tested

- `python -m compileall -q expense_tracker tests`: completed successfully.
- Three focused formatter and CLI tests passed.
- `python -m unittest discover -s tests -v`: 26 tests passed.
- Direct boundary checks proved `0 expenses`, `1 expense`, and `2 expenses`.
- Rehearsed the actual CLI: empty export reported `Exported 0 expenses.`, one-row
  export reported `Exported 1 expense.`, two-row export reported
  `Exported 2 expenses.`, and one-row import reported `Imported 1 expense.`

### Pending

- Hands-on learner completion of the Version 1.5.1 formatter exercise.
- Continue the separate job-application API after functions, modules, and
  exceptions have been demonstrated through practical Python work.
- Later progression to PostgreSQL, queues, Docker, monitoring, an AI document
  assistant, and optional cloud deployment.

### Blocked

- Publishing the prepared job-application API remains blocked: the intended
  repository still does not exist and repository creation is unavailable through
  the connected GitHub actions. The starter bundle remains preserved separately;
  no unrelated repository was modified.

## 2026-10-18 — Filter by normalized category

### Completed

- Added an optional category filter to `ExpenseStore.list()`, with the same
  trimming, lowercasing, and length validation used when categories are stored.
- Supported month-only, category-only, and combined month/category selection
  without changing the behavior of unfiltered calls.
- Built the query from hard-coded condition fragments while keeping month and
  category values in SQLite parameters.
- Reused the filtered `list()` path from `summary()` and `export()` so displayed,
  totaled, and exported records follow one selection rule.
- Added `--category` to the `list`, `summary`, and `export` commands and updated
  the README, study guide, and development plan to Version 1.5.

### Tested

- `python -m compileall -q expense_tracker tests`: completed successfully.
- Two focused category-filter tests passed.
- `python -m unittest discover -s tests -v`: 25 tests passed.
- Verified normalization of `" FOOD "`, category-only totals, a combined month
  and category filter, filtered CSV contents, and rejection of an empty category.
- Rehearsed the CLI with three expenses across two categories and two months:
  combined `list` returned only October food, category `summary` totaled both food
  rows at NGN 2,000.00, and combined `export` wrote only the October food row.

### Pending

- Hands-on learner completion of the Version 1.5 combined-filter exercise.
- Continue the separate job-application API after functions, modules, and
  exceptions have been demonstrated through hands-on Python work.
- Later progression to PostgreSQL, queues, Docker, monitoring, an AI document
  assistant, and optional cloud deployment.

### Blocked

- Publishing the prepared job-application API remains blocked: its intended
  repository still does not exist and repository creation is unavailable through
  the connected GitHub actions. Its starter bundle remains preserved separately;
  no unrelated repository was modified.

## 2026-10-17 — Reject malformed CSV syntax atomically

### Completed

- Enabled strict parsing in `csv.DictReader` so an unclosed quoted field raises
  `csv.Error` instead of being accepted as ordinary note text.
- Converted parser failures into the import method's public `ValueError` contract
  with a clear `CSV line N: malformed CSV` message.
- Reported the physical failing line from the underlying CSV reader, including
  failures that interrupt `DictReader` before it updates its own line counter.
- Preserved the two-phase design: syntax parsing and row validation still finish
  before the database insert transaction begins.
- Updated the README, study guide, and development plan to Version 1.4.2.

### Tested

- `python -m compileall -q expense_tracker tests`: completed successfully.
- Five targeted import tests passed.
- `python -m unittest discover -s tests -v`: 23 tests passed.
- Verified a file with a valid line 2 and an unclosed quote on line 3 reports line
  3, imports neither CSV row, and preserves the destination's original row.
- Re-ran export round-trip, bad-header, extra-field, invalid-value, UTF-8 BOM, and
  CLI import coverage to guard against regressions.
- Rehearsed the installed CLI against a temporary database: `add` created expense
  #1, malformed `import` exited with status 2 and named line 3, and both `show 1`
  and `list` confirmed the original expense was the only stored row.

### Pending

- Hands-on learner completion of the Version 1.4.2 malformed-CSV exercise.
- The separate job-application API, followed later by PostgreSQL, queues, Docker,
  monitoring, an AI document assistant, and optional cloud deployment.

### Blocked

- Publishing the prepared job-application API remains blocked: the intended
  repository still does not exist and repository creation is unavailable through
  the connected GitHub actions. No unrelated repository was modified.

## 2026-10-16 — Validate deletion IDs before SQL

### Completed

- Reused `valid_expense_id()` at the start of `ExpenseStore.delete()` so deletion
  now follows the same positive-integer contract as `get()` and `update()`.
- Rejected booleans explicitly even though Python treats `bool` as an `int`
  subclass, and rejected numeric-looking strings instead of relying on SQLite
  type conversion.
- Ensured validation happens before `delete()` opens its query connection or
  prepares a `DELETE` statement.
- Kept the existing missing-record behavior: a valid but absent ID still returns
  `False`, while malformed IDs raise `ValueError`.
- Updated the README, study guide, and development plan to Version 1.4.1.

### Tested

- `python -m compileall -q expense_tracker tests`: completed successfully.
- Three targeted deletion tests passed.
- `python -m unittest discover -s tests -v`: 22 tests passed.
- Verified direct deletion rejects `0`, `-1`, `True`, and `"1"`, then proved the
  original row still exists.
- Verified `delete -1 --yes` exits with status 2, prints the positive-integer rule,
  and leaves the stored row unchanged.
- Ran add/rejected-delete/show/confirmed-delete/list end to end: the rejected
  command preserved expense 1, the confirmed valid command removed it, and the
  final list was empty.

### Pending

- Hands-on learner completion of the Version 1.4.1 deletion exercise.
- The separate job-application API, followed later by PostgreSQL, queues, Docker,
  monitoring, an AI document assistant, and optional cloud deployment.

### Blocked

- Publishing the prepared job-application API remains blocked: the intended
  repository still does not exist, repository creation is absent from the
  connected GitHub actions, and no connected browser session was available.
  No unrelated repository was modified.

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
