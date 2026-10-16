# Python Expense Tracker — Version 1.4.1 Study Guide

## 1. What this project does

The application records personal expenses in Nigerian naira, saves them in a local
SQLite database, and lets a user:

- add an expense;
- show one expense by its unique ID;
- update selected fields on an existing expense;
- list all expenses or one month's expenses;
- summarize spending by category;
- export selected records to CSV;
- import validated CSV records atomically; and
- permanently delete a confirmed record.

It runs in a terminal. It is not a website and does not use a cloud service. The
learning goals are Python values and functions, command parsing, validation,
classes, SQL, persistence, exact monetary arithmetic, error handling, and tests.

## 2. Setup and a safe practice database

Install Python 3.10 or newer. Open a terminal in the downloaded or cloned project
folder. Use a disposable database while learning:

```sh
python -m expense_tracker --db practice.db add 4500 groceries --date 2026-10-14 --note "Rice and vegetables"
python -m expense_tracker --db practice.db add 2000 data --date 2026-10-14 --note "Weekly mobile data"
python -m expense_tracker --db practice.db update 1 --amount 5200.50 --category household --note ""
python -m expense_tracker --db practice.db show 1
python -m expense_tracker --db practice.db list
python -m expense_tracker --db practice.db summary --month 2026-10
python -m expense_tracker --db practice.db export practice.csv --month 2026-10
python -m expense_tracker --db restored.db import practice.csv
python -m expense_tracker --db restored.db summary --month 2026-10
python -m unittest discover -s tests -v
```

On Windows, `py` can replace `python`. You must be inside the repository folder so
Python can find the `expense_tracker` package. The global `--db` option goes before
the command; command-specific arguments go after the command.

The expected monthly total is NGN 7,200.50 in both databases. The import creates
new IDs; it does not copy IDs from `practice.csv`. Running the two `add` commands
or the import again creates duplicate expenses because duplicate detection is not
implemented.

## 3. Command behavior

| Command | Purpose | Important result |
| --- | --- | --- |
| `add AMOUNT CATEGORY` | Validate and save one expense | Prints its generated ID |
| `show ID` | Retrieve exactly one expense | Prints one row or exits with status 2 |
| `update ID [OPTIONS]` | Change only selected fields | Prints the updated row |
| `list` | Retrieve matching expenses | Newest date and ID first |
| `summary` | Add amounts by category | Prints category totals and grand total |
| `export PATH` | Write matching rows to CSV | Overwrites the destination file |
| `import PATH` | Validate and insert every CSV row | Writes all rows or none |
| `delete ID --yes` | Permanently remove a row | Requires a positive ID and confirmation |

`--month YYYY-MM` works with `list`, `summary`, and `export`.

## 4. Project architecture

| File | Responsibility |
| --- | --- |
| `expense_tracker/__init__.py` | Marks the directory as a Python package |
| `expense_tracker/__main__.py` | Parses commands, selects behavior, prints results |
| `expense_tracker/core.py` | Validation, money conversion, persistence, summaries, CSV I/O |
| `tests/test_tracker.py` | Verifies behavior with isolated temporary databases |
| `README.md` | Quick public overview and runnable examples |
| `docs/STUDY_GUIDE.md` | Detailed learning reference and exercises |
| `docs/DEVELOPMENT_LOG.md` | Dated completed, tested, pending, and blocked work |
| `docs/NEXT_STEPS.md` | Planned features that are not yet complete |

The command-line interface depends on the storage layer, but the storage layer does
not depend on terminal printing. This lets a future web API call `ExpenseStore`
methods without pretending to be a terminal user.

```text
terminal text -> argparse -> main() -> ExpenseStore -> SQLite file
                                  -> formatting -> terminal output
```

This separation is enough for a small project. A larger service would normally
split request models, business services, repositories, migrations, and logging.

## 5. What changed in Version 1.4.1

Version 1.4.1 is a small deletion-safety patch. `get()` and `update()` already
required a positive integer ID, but `delete()` previously sent its argument
straight to SQLite. A direct Python caller could therefore pass values outside the
documented ID contract. Destructive operations should validate at least as
strictly as read and update operations.

### The Python type trap

Python makes `bool` a subclass of `int`:

```python
isinstance(True, int)  # True
int(True)              # 1
```

That is convenient for some arithmetic, but unsafe for an expense ID. Without the
explicit boolean check in `valid_expense_id()`, `True` could behave like ID 1.
Numeric-looking strings such as `"1"` also do not satisfy the method's Python API
contract, even if a database engine can compare them with an integer column.

Parameterized SQL protects SQL structure from injection; it does not decide
whether a value is meaningful for the application. Domain validation and SQL
parameters solve different problems, so this code uses both.

### Changed function

`ExpenseStore.delete()` now validates before opening a connection:

```python
def delete(self, expense_id):
    expense_id = valid_expense_id(expense_id)
    with self.connect() as conn:
        cursor = conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        return cursor.rowcount > 0
```

Reusing the shared helper keeps one ID rule across `get()`, `update()`, and
`delete()`. A malformed ID raises `ValueError`. A well-formed positive integer
that is not stored still returns `False`; malformed input and a missing record are
different outcomes.

### Execution trace: rejected direct call

For `store.delete(True)`:

1. `delete()` immediately calls `valid_expense_id(True)`.
2. The helper checks `isinstance(value, bool)` before accepting integers.
3. It raises `ValueError("Expense ID must be a positive integer.")`.
4. `self.connect()` is never called and no `DELETE` statement is prepared.
5. The regression test retrieves the original row and proves it still exists.

### Execution trace: rejected CLI command

For `python -m expense_tracker --db practice.db delete -1 --yes`:

1. `argparse` converts the text `-1` to integer `-1` and records confirmation.
2. `main()` calls `store.delete(-1)`.
3. `valid_expense_id()` rejects the nonpositive value before SQL.
4. `main()` catches the `ValueError`; `parser.error()` prints the rule and exits
   with status 2.
5. The test confirms the existing expense count is unchanged.

This patch deliberately adds no new command. It strengthens an existing contract,
which is valuable maintenance work even though the production change is one line.

## 6. What changed in Version 1.4

Version 1.4 adds an atomic CSV import path. “Atomic” means one import is treated as
a unit: all valid rows are stored, or an error leaves the database unchanged. The
CLI accepts either of these exact header orders:

```text
amount_ngn,category,date,note
id,amount_ngn,category,date,note
```

The second form is the file produced by this application's `export` command. The
source `id` values are deliberately ignored; SQLite allocates fresh IDs that do
not collide with rows already in the destination database. A header-only file is
valid and imports zero expenses.

### Changed constants and functions

- `IMPORT_COLUMNS` defines the four fields that become a new expense.
- `EXPORT_COLUMNS` adds `id` in front of those fields. `export()` now writes this
  shared constant so the exporter and importer cannot silently disagree.
- `ExpenseStore.import_csv(path)` reads, validates, and inserts a CSV file.
- `main()` now exposes that method as `import PATH` and prints the inserted count.

The method opens files with `utf-8-sig`. Normal UTF-8 still works, while a UTF-8
byte-order mark from some spreadsheet tools is removed before checking the first
header name.

### Two-phase all-or-nothing design

The first phase does not write to SQLite. `csv.DictReader` checks the header and
turns each CSV row into a dictionary. Every row must have the exact number of
fields. The existing validators then convert the row into a tuple:

```python
(
    money_to_kobo(row["amount_ngn"]),
    normalize_category(row["category"]),
    valid_date(row["date"]),
    normalize_note(row["note"]),
)
```

Valid tuples are kept in the in-memory `records` list. If validation fails, the
method raises a new `ValueError` containing the physical CSV line number and keeps
the original reason as its exception cause.

Only after the whole file passes does the second phase open a database connection.
`executemany()` inserts all prepared tuples inside the connection's single
transaction. SQLite rolls that transaction back if an insert fails. This gives two
layers of protection: normal input failures occur before a write, and database
failures roll back the transaction.

### Successful command trace

For `python -m expense_tracker --db restored.db import practice.csv`:

1. `argparse` stores `import` as the command and the file name as `args.path`.
2. `ExpenseStore` initializes `restored.db` if it does not exist.
3. `import_csv()` validates the header and converts every data row.
4. The exported `id` column is read for shape checking but is not inserted.
5. One `executemany()` call inserts the prepared values and SQLite generates IDs.
6. The transaction commits and the method returns the number of inserted rows.
7. The CLI prints `Imported 2 expenses.` in the documented practice workflow.

### Failure trace and atomicity

Assume line 2 is valid and line 3 has amount `0`:

1. The validated line-2 tuple is appended only to the in-memory list.
2. `money_to_kobo("0")` rejects line 3 because the amount is not greater than zero.
3. `import_csv()` raises an error beginning `CSV line 3:`.
4. Execution never reaches the database connection or `executemany()`.
5. A test queries the destination and proves it still contains only its original
   row; line 2 was never partially imported.

Exact headers make accidental column swaps visible instead of guessing. Holding
the prepared rows in memory keeps the beginner implementation clear, but it also
means this version is intended for small personal files rather than huge imports.

## 7. What changed in Version 1.3

Version 1.3 adds a partial-update path. A user chooses one or more of `--amount`,
`--category`, `--date`, and `--note`; every omitted field keeps its existing value.
The command rejects an empty set of changes, invalid values, and missing IDs with
clear errors.

### Shared validation functions

Three small functions now hold rules used by more than one operation:

- `valid_expense_id(value)` requires a positive integer and rejects booleans;
- `normalize_category(value)` trims, lowercases, and enforces 1–50 characters;
- `normalize_note(value)` trims and enforces at most 500 characters.

`ExpenseStore.add()` now calls the category and note helpers instead of duplicating
their logic. `ExpenseStore.get()` calls the ID helper. Their observable behavior is
unchanged, but `add`, `get`, and `update` now share one source of truth for these
rules.

### `ExpenseStore.update(...)`

The new keyword-only method has this interface:

```python
def update(
    self, expense_id, *, amount=None, category=None, spent_on=None, note=None
):
    ...
```

`None` means “this field was not supplied.” An empty note is different: `note=""`
is a real change that clears the stored note. This distinction lets the command
preserve omitted fields while still supporting an intentional empty value.

The method validates all supplied values and builds a `changes` dictionary. If the
dictionary is empty, it raises `ValueError`. Otherwise, it creates an assignment
list such as `amount_kobo=?, category=?`. The column names come only from hard-coded
program keys; user values remain separate SQL parameters. One `UPDATE` statement
changes all selected fields in a single transaction.

The method returns the updated `sqlite3.Row`. It returns `None` for a well-formed
ID that is not present, allowing the CLI to choose the user-facing error message.

### CLI command

The command-line layer maps flags to keyword arguments:

```sh
python -m expense_tracker --db practice.db update 1 \
  --amount 5200.50 --category household --note ""
```

Observed output from the tested workflow:

```text
Updated #1 | 2026-10-14 | NGN 5,200.50 | household |
```

The final empty field shows that the note was deliberately cleared.

### Execution trace: partial update

1. `argparse` converts the ID to integer `1`; absent `--date` becomes `None`.
2. `main()` calls `store.update()` with the supplied strings.
3. `valid_expense_id()` accepts `1`.
4. `money_to_kobo("5200.50")` produces integer `520050`.
5. `normalize_category("household")` returns `"household"` and
   `normalize_note("")` returns an empty string.
6. `changes` contains amount, category, and note, but not the date.
7. SQLite executes one parameterized `UPDATE`, so the original date is preserved.
8. A `SELECT` retrieves the new row and `format_expense()` prepares the output.

If any supplied value is invalid, validation raises before the update statement.
If no flags are supplied, the empty `changes` dictionary is rejected. Tests verify
that the original row remains unchanged after each rejected attempt.

## 8. What changed in Version 1.2

Version 1.2 turns two documented input limits into executable contracts. No
runtime function changed: `ExpenseStore.add()` already enforced the limits. The
new work adds tests that prove both the last accepted value and first rejected
value, then documents realistic commands that use a disposable database.

### `test_category_length_boundaries()`

This test constructs a 50-character category, surrounds it with spaces, and uses
uppercase letters. `ExpenseStore.add()` trims and lowercases the value before
checking its length, so the stored result is 50 lowercase characters. A second
call supplies 51 characters and must raise the documented `ValueError`. The test
then proves that the failed call did not add a row.

### `test_note_length_boundaries()`

This test follows the same boundary pattern for notes: a trimmed 500-character
note is stored exactly, a 501-character note is rejected, and only the accepted
record remains in the database.

### Why exact boundaries matter

Testing an ordinary short value does not prove that the maximum works. Testing
only an oversized value does not prove that the code is not too strict. For a
maximum `N`, the most informative examples are usually `N` and `N + 1`; adding
`N - 1` can be useful when the rule is more complicated.

The changed functions in this milestone are test methods, not production
functions. That is still useful portfolio work: the tests reduce the chance that
a later refactor silently changes a public validation rule.

### Boundary execution trace

For `maximum_category = "A" * 50`:

1. The test calls `add()` with a leading and trailing space.
2. `money_to_kobo()` and `valid_date()` validate the other fields.
3. `category.strip().lower()` removes the spaces and produces 50 lowercase `a`
   characters.
4. `len(category) > 50` is false, so SQLite inserts the row.
5. `get(record_id)` retrieves it and the test checks the normalized value.

For `"b" * 51`, the length check is true. `add()` raises `ValueError` before the
`INSERT`, and the final row-count assertion proves that no partial record appeared.

## 9. What changed in Version 1.1

### `ExpenseStore.get(expense_id)`

The new method checks that the ID is a positive integer, runs a parameterized
`SELECT`, and returns either one `sqlite3.Row` or `None`.

```python
def get(self, expense_id):
    if isinstance(expense_id, bool) or not isinstance(expense_id, int) or expense_id <= 0:
        raise ValueError("Expense ID must be a positive integer.")
    with self.connect() as conn:
        return conn.execute(
            "SELECT * FROM expenses WHERE id=?", (expense_id,)
        ).fetchone()
```

The `bool` check is intentional: in Python, `isinstance(True, int)` is true. An ID
of `True` would otherwise behave like integer 1 for direct callers.

Returning `None` for a well-formed but missing ID keeps the storage method reusable.
The CLI decides that a missing record should become a user-facing command error.

### `format_expense(row)`

Before this milestone, `list` built its output string inline. The new helper creates
one representation used by both `list` and `show`. A future output change can now
be made in one place.

### `show ID` command path

`argparse` converts the terminal ID text to an integer. `main()` calls `store.get()`.
If the result is `None`, `parser.error()` prints an error and exits with status 2.
Otherwise the row is printed through `format_expense()`.

### Regression tests

Two tests were added:

- storage lookup covers an existing ID, a missing ID, and invalid direct inputs;
- CLI lookup covers exact printed output and the missing-ID exit status.

The suite had 12 tests at Version 1.1, 14 after Version 1.2, and 17 after
Version 1.3.

## 10. Execution trace: `show 1`

Assume expense 1 already exists.

1. Python executes `expense_tracker/__main__.py`.
2. `argparse` recognizes `show` and converts the text `"1"` to integer `1`.
3. `ExpenseStore` opens or initializes the selected SQLite database.
4. `main()` calls `store.get(1)`.
5. `get()` validates the ID.
6. SQLite receives fixed SQL plus a separate tuple `(1,)`.
7. `fetchone()` returns one `sqlite3.Row`, or `None` if no row matches.
8. `format_expense()` reads named columns such as `row["amount_kobo"]`.
9. `format_money(520050)` produces `NGN 5,200.50`.
10. The CLI prints the completed line.

Observed output from the tested practice run:

```text
#1 | 2026-10-14 | NGN 5,200.50 | household |
```

For `show 999`, the observed message was `Expense ID not found.` and the process
returned status 2. That nonzero status lets scripts distinguish success from error.

## 11. Trace an added expense

For `python -m expense_tracker --db practice.db add 4500 groceries`:

1. `parse_args()` creates a namespace containing command `add`, amount string
   `"4500"`, category `"groceries"`, and today's local date unless `--date` is supplied.
2. `ExpenseStore(args.db)` initializes the table if necessary.
3. `add()` calls `money_to_kobo()` and `valid_date()`.
4. The amount becomes integer `450000` kobo, not floating-point `4500.0`.
5. The category is trimmed and lowercased; the note is trimmed.
6. SQLite executes a parameterized `INSERT` and generates the record ID.
7. The transaction commits, `add()` returns the ID, and the CLI prints it.

Predict each value before running the command. That is more useful than memorizing
the final code.

## 12. Core Python functions and decisions

### `money_to_kobo(value)`

`Decimal` represents decimal input exactly. The function converts `"12.50"` to
integer `1250`, rejects NaN and infinity, rejects zero and negatives, enforces a
maximum, and refuses fractional kobo such as `1.001` naira. It does not silently
round invalid money.

### `format_money(kobo)`

The function divides by 100 with `Decimal`, adds comma separators, and always shows
two decimal places.

### `valid_date(value)` and `valid_month(value)`

A regular expression checks the required text shape. The date library checks the
calendar. Shape alone would accept February 30, so both checks matter.

### `csv_safe(value)`

Spreadsheet programs may interpret text beginning with `=`, `+`, `-`, or `@` as a
formula. The function prefixes an apostrophe when a user-controlled category or
note begins with such a character after whitespace. This is a conservative export
defense; spreadsheet behavior still varies.

## 13. Classes, state, and SQLite

`ExpenseStore` is a class. Each instance stores its database path in `self.path`.
`self` means the particular object on which a method was called.

`__init__` creates the parent folder and runs `CREATE TABLE IF NOT EXISTS`. It does
not migrate an older schema if the columns change later.

| Column | Meaning |
| --- | --- |
| `id` | Unique integer identifier |
| `amount_kobo` | Positive integer monetary amount |
| `category` | Trimmed, lowercase category, maximum 50 characters |
| `spent_on` | Validated `YYYY-MM-DD` date text |
| `note` | Optional description, maximum 500 characters |

`sqlite3.Row` supports readable names such as `row["category"]`. The connection
context handles transactions, and the helper closes each connection.

All SQL values use `?` placeholders. Never replace them with string interpolation.
A note that looks like SQL remains data rather than becoming a command.

## 14. Tests and verified behavior

Run:

```sh
python -m unittest discover -s tests -v
```

The 2026-10-16 milestone run reported:

```text
Ran 22 tests
OK
```

Tests use a fresh temporary folder and database for each test. They cover exact
money conversion, rejected money and dates, exact 50/51-character category and
500/501-character note boundaries, persistence after reopening, sorting, monthly
filtering and totals, single-record lookup, valid partial updates, rejected updates,
missing update IDs, note clearing, SQL-looking text, CSV escaping, deletion,
confirmation, rejected deletion IDs with row preservation, export-to-import
behavior, fresh imported IDs, atomic rejection of an invalid later row, malformed
CSV shapes, and real CLI paths.

A passing suite proves only the listed cases passed in that environment. It does
not prove the absence of every bug, production performance, or security readiness.

## 15. Current limitations

- Single local user; no accounts, authentication, or per-user authorization.
- NGN only; the schema cannot safely mix currencies.
- No duplicate detection, undo, or audit history. Importing the same file twice
  creates two sets of expenses.
- CSV import requires one of two exact header orders, generates fresh IDs, and
  holds every prepared row in memory before inserting.
- Formula-like text protected by export begins with an apostrophe. Import treats
  that apostrophe as literal data because removing it would be ambiguous.
- No schema migration tool.
- Text limits use Python's `len()` after trimming. There is no Unicode
  normalization or separate UTF-8 byte limit.
- No encryption; anyone who can read the database file can read its contents.
- CSV export overwrites the target path.
- A valid confirmed deletion is immediate and has no undo or audit record.
- No API, browser interface, PostgreSQL, Docker, monitoring, or cloud deployment.
- No measured production users, reliability, load, or business impact.

These are scope boundaries, not hidden completed features.

## 16. Interview questions and honest answers

**Why does ID validation reject `True` before checking `int`?**
`bool` inherits from `int` in Python, so `isinstance(True, int)` is true. The
explicit boolean check prevents `True` from behaving like expense ID 1.

**Why is parameterized SQL not enough for deletion safety?**
Parameters stop a value from changing SQL syntax, but SQLite can still receive a
value that violates the application's ID rules. Validation checks meaning;
parameterization protects query structure.

**Why validate before `delete()` opens its query connection?**
Invalid input needs no database work. Failing early makes the control flow easier
to reason about and proves destructive SQL was never reached.

**Why validate the full CSV before inserting its first row?**
It prevents a late bad row from leaving an incomplete import. Valid rows exist only
as Python tuples until every row passes.

**Why also use one database transaction?**
Validation cannot predict every database error. A single transaction makes SQLite
roll back earlier inserts if an insert operation fails.

**Why ignore IDs from the imported file?**
An ID is meaningful only inside its source database. Reusing it could collide with
an existing row or overwrite the destination's identity rules. SQLite safely
generates the next local IDs.

**Why require exact headers instead of guessing similar column names?**
Silent guesses can put a date or amount into the wrong field. An explicit contract
fails early and tells the user how to fix the file.

**Why are the update fields keyword-only?**
The `*` in the method signature prevents an unclear call such as
`update(1, "20", "food")`. Names make each optional change explicit and reduce
the chance of putting a value in the wrong field.

**Why does `None` mean omitted while an empty note means clear it?**
Partial updates need to distinguish “leave this alone” from “set this to empty.”
The CLI naturally produces `None` for an absent flag and `""` for `--note ""`.

**Is the dynamic update SQL vulnerable to user-supplied column names?**
The assignment names come only from hard-coded dictionary keys in the program.
Every user-controlled value is still bound through a `?` placeholder.

**Why return the updated row?**
The CLI can immediately show the final persisted state, and a future API can use
the same result without issuing its own lookup.

**Why test 50 and 51 characters instead of one ordinary category?**
They sit on opposite sides of the stated maximum, so together they prove the
inclusive boundary. An ordinary short category cannot detect an off-by-one bug.

**Why check the database row count after a validation error?**
It verifies more than the exception message: rejected input must not create a
partial or hidden record.

**Why was no production function changed in Version 1.2?**
The behavior was already correct. Adding regression evidence was safer than
rewriting working code simply to make a larger diff.

**Why add `get()` instead of filtering `list()` in Python?**
The database can find one primary-key row directly. The method also expresses the
intent clearly and avoids retrieving unrelated rows.

**Why can `get()` return `None`?**
A positive integer can be valid input even when no record currently has that ID.
The storage layer reports absence; the CLI chooses the user-facing error.

**Why share `format_expense()`?**
Both commands show the same record shape. One helper avoids duplicated formatting
and inconsistent future changes.

**How is SQL injection reduced?**
The application keeps SQL structure fixed and binds user values separately through
placeholders.

**Why store money as integer kobo?**
Whole kobo sums exactly. `Decimal` safely handles conversion and display. Supporting
multiple currencies would require additional rules and schema fields.

**What would change for a cloud API?**
Add HTTP routes, request and response schemas, authentication, authorization,
migrations, PostgreSQL, configuration, structured logging, metrics, deployment,
and API integration tests. Those features are not implemented here.

**How was the project built?**
Development used AI assistance. A truthful answer should distinguish generated or
assisted implementation from the code personally studied, changed, and tested.

## 17. Hands-on exercises

Do these locally; reading alone is not practical mastery.

### Exercise A — Import and explain

Create `manual.csv` with the four-column header and two expense rows. Import it into
a new database, list the records, and explain why their IDs were generated locally.

### Exercise B — Follow the import variables

For the first CSV row, write down the type and value of `reader.fieldnames`, `row`,
`line_number`, and the tuple added to `records`. Use temporary `print()` calls to
check your predictions, then remove them and return the suite to green.

### Exercise C — Observe a failing test

Temporarily replace `normalize_category(row["category"])` with the raw value. Run
the import tests, identify the assertion that catches the regression, restore the
code, and rerun all tests.

### Exercise D — Prove atomicity yourself

Make a CSV whose first data row is valid and whose second has an impossible date.
Import it, read the reported line number, then run `list` and prove that neither
row was added.

### Exercise E — Revisit partial updates

Add two expenses, update only the category of the first, and prove with `show` that
its amount, date, and note did not change.

### Exercise F — Connect the next project

Write pseudocode for a future `POST /applications` FastAPI route. Mark which input
rules belong in an HTTP request model and which belong in reusable domain logic.
Do not claim or deploy the API until its separate repository and tests exist.

### Exercise G — Prove deletion safety

Add one expense, then call `delete -1 --yes` and confirm it exits with an error.
Run `show 1` to prove the row remains. Finally, explain why `True`, `"1"`, and `1`
are three different inputs even though Python or SQLite may compare some of them
similarly.

## 18. Readiness check

You understand Version 1.4.1 when you can run every command unaided, explain why
`bool` is an `int` subclass but not a valid ID, distinguish validation from SQL
parameterization, trace a rejected delete before `delete()` opens its query
connection, prove the stored row remains, make a small local change, observe the
deletion test fail, restore the behavior, and return all 22 tests to green.
