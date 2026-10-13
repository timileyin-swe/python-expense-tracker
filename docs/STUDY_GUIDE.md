# Python Expense Tracker — Version 1.2 Study Guide

## 1. What this project does

The application records personal expenses in Nigerian naira, saves them in a local
SQLite database, and lets a user:

- add an expense;
- show one expense by its unique ID;
- list all expenses or one month's expenses;
- summarize spending by category;
- export selected records to CSV; and
- permanently delete a confirmed record.

It runs in a terminal. It is not a website and does not use a cloud service. The
learning goals are Python values and functions, command parsing, validation,
classes, SQL, persistence, exact monetary arithmetic, error handling, and tests.

## 2. Setup and a safe practice database

Install Python 3.10 or newer. Open a terminal in the downloaded or cloned project
folder. Use a disposable database while learning:

```sh
python -m expense_tracker --db practice.db add 4500 groceries --date 2026-10-13 --note "Rice and vegetables"
python -m expense_tracker --db practice.db add 2000 data --date 2026-10-13 --note "Weekly mobile data"
python -m expense_tracker --db practice.db show 1
python -m expense_tracker --db practice.db list
python -m expense_tracker --db practice.db summary --month 2026-10
python -m expense_tracker --db practice.db export practice.csv --month 2026-10
python -m unittest discover -s tests -v
```

On Windows, `py` can replace `python`. You must be inside the repository folder so
Python can find the `expense_tracker` package. The global `--db` option goes before
the command; command-specific arguments go after the command.

The expected monthly total is NGN 6,500.00. Running the two `add` commands again
creates two more records, because duplicate detection is not implemented.

## 3. Command behavior

| Command | Purpose | Important result |
| --- | --- | --- |
| `add AMOUNT CATEGORY` | Validate and save one expense | Prints its generated ID |
| `show ID` | Retrieve exactly one expense | Prints one row or exits with status 2 |
| `list` | Retrieve matching expenses | Newest date and ID first |
| `summary` | Add amounts by category | Prints category totals and grand total |
| `export PATH` | Write matching rows to CSV | Overwrites the destination file |
| `delete ID --yes` | Permanently remove a row | Refuses to run without confirmation |

`--month YYYY-MM` works with `list`, `summary`, and `export`.

## 4. Project architecture

| File | Responsibility |
| --- | --- |
| `expense_tracker/__init__.py` | Marks the directory as a Python package |
| `expense_tracker/__main__.py` | Parses commands, selects behavior, prints results |
| `expense_tracker/core.py` | Validation, money conversion, persistence, summaries, export |
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

## 5. What changed in Version 1.2

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

## 6. What changed in Version 1.1

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

The suite had 12 tests at Version 1.1 and has 14 after Version 1.2.

## 7. Execution trace: `show 1`

Assume expense 1 already exists.

1. Python executes `expense_tracker/__main__.py`.
2. `argparse` recognizes `show` and converts the text `"1"` to integer `1`.
3. `ExpenseStore` opens or initializes the selected SQLite database.
4. `main()` calls `store.get(1)`.
5. `get()` validates the ID.
6. SQLite receives fixed SQL plus a separate tuple `(1,)`.
7. `fetchone()` returns one `sqlite3.Row`, or `None` if no row matches.
8. `format_expense()` reads named columns such as `row["amount_kobo"]`.
9. `format_money(450000)` produces `NGN 4,500.00`.
10. The CLI prints the completed line.

Observed output from the tested practice run:

```text
#1 | 2026-10-13 | NGN 4,500.00 | groceries | Rice and vegetables
```

For `show 999`, the observed message was `Expense ID not found.` and the process
returned status 2. That nonzero status lets scripts distinguish success from error.

## 8. Trace an added expense

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

## 9. Core Python functions and decisions

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

## 10. Classes, state, and SQLite

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

## 11. Tests and verified behavior

Run:

```sh
python -m unittest discover -s tests -v
```

The 2026-10-13 milestone run reported:

```text
Ran 14 tests
OK
```

Tests use a fresh temporary folder and database for each test. They cover exact
money conversion, rejected money and dates, exact 50/51-character category and
500/501-character note boundaries, persistence after reopening, sorting, monthly
filtering and totals, single-record lookup, invalid IDs, SQL-looking text, CSV
escaping, deletion, confirmation, and real CLI paths.

A passing suite proves only the listed cases passed in that environment. It does
not prove the absence of every bug, production performance, or security readiness.

## 12. Current limitations

- Single local user; no accounts, authentication, or per-user authorization.
- NGN only; the schema cannot safely mix currencies.
- No update command, duplicate detection, undo, or audit history.
- No atomic CSV import.
- No schema migration tool.
- Text limits use Python's `len()` after trimming. There is no Unicode
  normalization or separate UTF-8 byte limit.
- No encryption; anyone who can read the database file can read its contents.
- CSV export overwrites the target path.
- No API, browser interface, PostgreSQL, Docker, monitoring, or cloud deployment.
- No measured production users, reliability, load, or business impact.

These are scope boundaries, not hidden completed features.

## 13. Interview questions and honest answers

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

## 14. Hands-on exercises

Do these locally; reading alone is not practical mastery.

### Exercise A — Run and explain

Add two expenses to `practice.db`, use `show` for each ID, and explain every field
in the printed line without reading this guide.

### Exercise B — Follow the variables

For `show 1`, write down the type and value of `args.id`, `expense_id`, `row`, and
`row["amount_kobo"]` at each step. Then use temporary `print(type(...))` statements
to check your predictions and remove them afterward.

### Exercise C — Observe a failing test

Temporarily change `format_expense()` so it omits the category. Run the tests,
identify the failing assertion, restore the code, and run the suite again.

### Exercise D — Explore the boundary tests

Read `test_category_length_boundaries()` and predict every assertion. Then run only
that test. Change the accepted input locally to 49 characters, rerun it, explain
why the stored-value assertion fails, and restore the original test.

### Exercise E — Design before coding

Write pseudocode for `update ID --amount ... --category ...`. Decide what happens
when no fields are provided, the ID is missing, or one new value is invalid. This
prepares the next feature without pretending it is implemented.

## 15. Readiness check

You understand Version 1.2 when you can run every command unaided, trace both
`add` and `show`, explain why 50 characters pass while 51 fail, distinguish a
missing row from an invalid ID, predict a monthly total, identify the database
file, make a small local change, observe a relevant test fail, restore the
behavior, and return the suite to green.
