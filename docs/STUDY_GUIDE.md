# Python Expense Tracker — Version 1.7 Study Guide

## 1. What this project does

The application records personal expenses in Nigerian naira, saves them in a local
SQLite database, and lets a user:

- add an expense;
- show one expense by its unique ID;
- update selected fields on an existing expense;
- list all expenses or filter them by month, category, or both;
- summarize spending by category;
- create or refresh a consistent database backup;
- export selected records to CSV or JSON;
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
python -m expense_tracker --db practice.db backup practice-backup.db
python -m expense_tracker --db practice.db show 1
python -m expense_tracker --db practice-backup.db show 1
python -m expense_tracker --db practice.db list --month 2026-10 --category household
python -m expense_tracker --db practice.db summary --month 2026-10
python -m expense_tracker --db practice.db summary --month 2026-10 --category household
python -m expense_tracker --db practice.db export practice.csv --month 2026-10
python -m expense_tracker --db practice.db export-json practice.json --month 2026-10
python -m json.tool practice.json
python -m expense_tracker --db restored.db import practice.csv
python -m expense_tracker --db restored.db summary --month 2026-10
python -m unittest discover -s tests -v
```

On Windows, `py` can replace `python`. You must be inside the repository folder so
Python can find the `expense_tracker` package. The global `--db` option goes before
the command; command-specific arguments go after the command.

The expected monthly total is NGN 7,200.50 in both imported databases. The backup
captures the complete state of `practice.db` at that moment, including the original
IDs. The import creates new IDs; it does not copy IDs from `practice.csv`. Running
the two `add` commands or the import again creates duplicate expenses because
duplicate detection is not implemented. The JSON command is export-only and does
not create another database.

## 3. Command behavior

| Command | Purpose | Important result |
| --- | --- | --- |
| `add AMOUNT CATEGORY` | Validate and save one expense | Prints its generated ID |
| `show ID` | Retrieve exactly one expense | Prints one row or exits with status 2 |
| `update ID [OPTIONS]` | Change only selected fields | Prints the updated row |
| `list` | Retrieve expenses matching optional filters | Newest date and ID first |
| `summary` | Add matching amounts by category | Prints category totals and grand total |
| `backup PATH` | Create or refresh a database snapshot | Rejects the live database as its destination |
| `export PATH` | Write filtered rows to CSV | Overwrites the file and reports a grammatical count |
| `export-json PATH` | Write filtered rows to readable JSON | Keeps exact money as decimal text |
| `import PATH` | Strictly parse, validate, and insert CSV | Writes all or none and reports a grammatical count |
| `delete ID --yes` | Permanently remove a row | Requires a positive ID and confirmation |

`--month YYYY-MM` and `--category CATEGORY` work independently or together with
`list`, `summary`, `export`, and `export-json`. Category matching is exact after
the same trimming and lowercasing used when an expense is added.

## 4. Project architecture

| File | Responsibility |
| --- | --- |
| `expense_tracker/__init__.py` | Marks the directory as a Python package |
| `expense_tracker/__main__.py` | Parses commands, selects behavior, prints results |
| `expense_tracker/core.py` | Validation, money conversion, persistence, backups, summaries, CSV/JSON I/O |
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

## 5. What changed in Version 1.7

Version 1.7 adds a JSON export that connects the current command-line project to a
core web-API concept: converting internal data into a documented public shape.

```sh
python -m expense_tracker --db practice.db export-json october-food.json \
  --month 2026-10 --category food
```

The output is one valid JSON array. A one-expense file has this shape:

```json
[
  {
    "id": 1,
    "amount_ngn": "1500.25",
    "category": "food",
    "date": "2026-10-21",
    "note": "Café lunch ₦"
  }
]
```

JSON has arrays, objects, strings, numbers, booleans, and `null`. The file uses a
JSON array because an export may contain zero, one, or many expense objects.

### New public row mapping

`expense_to_dict(row)` converts the SQLite-specific row into ordinary Python data:

```python
def expense_to_dict(row):
    """Convert one expense row to a JSON-compatible public representation."""
    return {
        "id": row["id"],
        "amount_ngn": f"{Decimal(row['amount_kobo']) / 100:.2f}",
        "category": row["category"],
        "date": row["spent_on"],
        "note": row["note"],
    }
```

This function defines a small serialization boundary. Internal names such as
`amount_kobo` and `spent_on` do not leak accidentally; the public record uses
`amount_ngn` and `date`. Its return value contains only an integer and strings,
which Python's standard JSON encoder supports directly.

| Python value | JSON value | Reason |
| --- | --- | --- |
| integer `id` | number | IDs are whole numbers |
| `amount_ngn` string | string | Preserves two exact decimal places |
| category/date/note strings | strings | Already validated text values |
| list of dictionaries | array of objects | Represents the selected collection |

The amount deliberately remains a string. Converting `1500.25` through a binary
`float` can introduce representation concerns, while the database already stores
exact integer kobo. Formatting from kobo to `"1500.25"` keeps a predictable API
contract. A future API client can decide how to display or convert that text.

### New JSON export method

`ExpenseStore.export_json()` reuses `list()` and writes one complete document:

```python
def export_json(self, path, month=None, category=None):
    """Write selected expenses as one human-readable JSON array."""
    records = [expense_to_dict(row) for row in self.list(month, category)]
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
        handle.write("\\n")
    return len(records)
```

The list comprehension calls the mapping once for every selected row. Python's
[`json.dump()` documentation](https://docs.python.org/3/library/json.html#json.dump)
describes writing a Python object to a text stream. Here:

- `ensure_ascii=False` keeps readable Unicode characters such as `é` and `₦`
  instead of replacing them with escape sequences;
- `indent=2` makes nested arrays and objects easy for a person to inspect;
- the final newline works cleanly with terminal tools; and
- the returned integer lets the CLI reuse `format_expense_count()`.

The entire list is written with one `json.dump()` call. Repeated calls on the same
file handle would place separate JSON values beside each other and create an
invalid document.

### CLI wiring and filter reuse

`main()` adds `export-json` to the same parser-building loop as `list`,
`summary`, and CSV `export`. Both export commands receive a path and the existing
`--month` and `--category` options. The command branch is intentionally small:

```python
count = store.export_json(args.path, args.month, args.category)
print(f"Exported {format_expense_count(count)} to JSON.")
```

There is no second SQL query implementation. `export_json()` calls `list()`, so
month validation, category normalization, parameterized SQL, ordering, and
combined-filter behavior remain in one tested place.

### Execution trace: filtered JSON export

For `export-json food.json --month 2026-10 --category " FOOD "`:

1. `argparse` records the destination and both filter strings.
2. `main()` calls `store.export_json(...)`.
3. `list()` validates the month, normalizes the category to `food`, and executes
   its parameterized query.
4. The list comprehension passes each returned `sqlite3.Row` to
   `expense_to_dict()`.
5. Integer kobo becomes exact two-decimal text; the other fields are copied into
   the documented public names.
6. `json.dump()` writes one indented UTF-8 array and the method adds a newline.
7. The method returns `1` and the CLI prints `Exported 1 expense to JSON.`

The verified rehearsal exported one food expense while excluding a data expense.
`python -m json.tool` accepted the document, and the tests parsed it again with
`json.loads()` before checking every field.

### Design decision and API bridge

JSON export is useful on its own for integrations and portfolio inspection, but
the reusable mapping is the more important Cloud-SWE lesson. A future FastAPI route
could obtain rows from a service and reuse the same plain dictionary shape before
the framework encodes an HTTP response. This project does not claim that an HTTP
API, request validation, authentication, or PostgreSQL exists yet.

This milestone intentionally adds export only. JSON import would need an explicit
schema, type validation, duplicate rules, atomic writes, size limits, and useful
item-level error locations rather than simply trusting `json.load()` output.

## 6. What changed in Version 1.6

Version 1.6 adds a safe, explicit database backup command:

```sh
python -m expense_tracker --db practice.db backup backups/practice.db
```

The command creates the destination folder when necessary, copies a consistent
SQLite snapshot, and prints the destination. It can also refresh an existing
backup. It refuses a destination that resolves to the live database itself.

This feature is more reliable than copying a database file with ordinary file
operations while it might be open. Python documents
[`sqlite3.Connection.backup()`](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup)
as the database backup operation and notes that it works while other clients are
accessing the database.

### Changed storage method

`ExpenseStore.backup(path)` belongs in `core.py` because it is persistence
behavior that can be reused by the CLI, tests, or a future API:

```python
def backup(self, path):
    """Create a consistent SQLite backup at a different path."""
    destination = Path(path)
    if destination.resolve() == self.path.resolve():
        raise ValueError("Backup path must be different from the database path.")
    destination.parent.mkdir(parents=True, exist_ok=True)

    with self.connect() as source:
        target = sqlite3.connect(destination)
        try:
            with target:
                source.backup(target)
        finally:
            target.close()
    return destination
```

`Path(path)` turns the input into a path object. `resolve()` produces an absolute,
normalized path, so `expenses.db` and an equivalent spelling such as
`folder/../expenses.db` compare as the same destination. This guard runs before
the target connection is opened.

`destination.parent.mkdir(parents=True, exist_ok=True)` creates every missing
parent folder. `parents=True` permits more than one missing level, while
`exist_ok=True` makes an existing folder acceptable.

### Connections, transactions, and cleanup

`self.connect()` opens the source connection through the class's existing context
manager. That helper commits or rolls back its transaction and closes the source
in a `finally` block.

The target connection has two separate responsibilities:

- `with target:` supplies transaction handling; and
- the outer `try`/`finally` guarantees `target.close()` even if the backup raises.

A transaction context and closing a resource are related but not identical.
Python's SQLite connection context manager manages the transaction; this method
closes the target explicitly. Closing both connections matters because operating
systems and SQLite may otherwise keep file handles or locks longer than intended.

The method returns the destination `Path` rather than printing. The CLI branch
owns presentation:

```python
path = store.backup(args.path)
print(f"Backed up database to {path}.")
```

### Execution trace: back up, then change the source

For `python -m expense_tracker --db live.db backup backups/snapshot.db`:

1. `argparse` stores `live.db` as the global database and selects `backup`.
2. `ExpenseStore` opens or initializes `live.db`.
3. `backup()` resolves the source and destination paths and proves they differ.
4. The destination's parent folder is created if it is missing.
5. The method opens source and target SQLite connections.
6. `source.backup(target)` copies a consistent snapshot into the target database.
7. The target is committed and closed; the source helper also closes its
   connection.
8. The method returns the `Path` and the CLI prints it.

The verified command rehearsal then updated and deleted expense 1 from the live
database. `list` reported no live expenses, while `show 1` against the backup still
returned its original NGN 1,500.00 amount and note. The files are independent after
the snapshot is created.

### Refresh behavior and failure boundary

If the destination already contains an older valid SQLite database, running
`backup` again refreshes it to the source's current state. The regression test
creates one snapshot, changes the source, proves the snapshot is unchanged, runs
backup again, and then proves the refreshed destination contains both current
rows.

The same-path guard raises `ValueError` before opening a target. The CLI catches
that error and exits through `parser.error()` with status 2. Other file and SQLite
failures, such as an unwritable destination, follow the command's existing
`OSError` and `sqlite3.Error` handling.

### Design decision

This is a whole-database snapshot, not record-level undo. It protects a user who
creates and verifies a backup before a destructive operation, while keeping the
implementation inside Python's standard library. There is intentionally no
automatic schedule, encryption, cloud upload, retention policy, or restore
command. A user can inspect a snapshot safely by selecting it with `--db`.

## 7. What changed in Version 1.5.1

Version 1.5.1 fixes a small but visible command-line grammar bug. The `export` and
`import` commands previously always added the word `expenses`, which produced
messages such as `Exported 1 expenses.` A portfolio project should handle the
edge cases users can see, even when the database behavior is already correct.

The commands now produce:

```text
Exported 0 expenses.
Exported 1 expense.
Exported 2 expenses.
Exported 1 expense to JSON.
Imported 1 expense.
```

### New pure formatting function

`expense_tracker/__main__.py` now defines:

```python
def format_expense_count(count):
    """Return a count with the grammatically correct expense label."""
    label = "expense" if count == 1 else "expenses"
    return f"{count} {label}"
```

This is a **function**: a named, reusable block of code. `count` is its parameter,
and `return` sends the completed string back to the caller. The function does not
print, read a file, or change the database, so it is also a **pure function** for
the integer inputs used by the CLI. The same input always produces the same output.

The expression `"expense" if count == 1 else "expenses"` is a **conditional
expression**. It chooses the singular word only when the count is exactly one.
Zero uses the plural in standard English, as do two and larger counts.

### Changed command paths

`export` and `import` now save the storage method's returned count in a variable,
pass it to the helper, and print the result:

```python
count = store.export(args.path, args.month, args.category)
print(f"Exported {format_expense_count(count)}.")
```

The import and JSON-export branches follow the same shape. Keeping the grammar in
one helper means the commands cannot drift into different singular/plural rules.

### Execution trace: exporting one expense

1. `argparse` selects the `export` branch and supplies the requested path and
   optional filters.
2. `ExpenseStore.export()` writes the matching rows and returns integer `1`.
3. `main()` assigns that value to `count`.
4. `format_expense_count(1)` evaluates `count == 1` as `True`.
5. The helper sets `label` to `"expense"` and returns `"1 expense"`.
6. The command prints `Exported 1 expense.`

For an empty selection, the storage method returns `0`. The condition is false,
so the helper returns `"0 expenses"`. For two rows it returns `"2 expenses"`.

### Design decision

The helper belongs in `__main__.py`, not `core.py`, because it controls human-facing
grammar rather than money, validation, or persistence. `ExpenseStore.export()`,
`export_json()`, and `import_csv()` return integers that a terminal, future API, or
test can present differently. The formatter is intentionally small and tested
directly at the important `0`, `1`, and `2` boundary values.

## 8. What changed in Version 1.5

Version 1.5 adds one consistent category filter to three existing commands. A user
can now select one normalized category with `list`, calculate only that category
with `summary`, or write only its rows with `export`. The category filter can be
used alone or combined with `--month`.

```sh
python -m expense_tracker --db practice.db list --category " Household "
python -m expense_tracker --db practice.db summary --month 2026-10 --category household
python -m expense_tracker --db practice.db export household.csv --month 2026-10 --category household
```

### Changed functions and CLI wiring

- `ExpenseStore.list(month=None, category=None)` now accepts both optional filters.
- `ExpenseStore.summary(month=None, category=None)` passes both filters to
  `list()` instead of implementing a separate selection rule.
- `ExpenseStore.export(path, month=None, category=None)` does the same before
  writing CSV.
- `main()` adds `--category` to the `list`, `summary`, and `export` parsers and
  forwards the parsed value.

Older calls such as `store.list()` and `store.list("2026-10")` still behave as
before because both optional parameters default to `None`.

### Building one safe query from optional conditions

`list()` starts with two empty lists:

```python
conditions = []
parameters = []
```

If a month is supplied, the method validates it and appends a hard-coded SQL
condition plus its value. If a category is supplied, `normalize_category()` trims
and lowercases it, then appends another hard-coded condition and value. Only the
program's fixed condition text becomes part of the SQL string:

```python
if month is not None:
    conditions.append("substr(spent_on,1,7)=?")
    parameters.append(valid_month(month))
if category is not None:
    conditions.append("category=?")
    parameters.append(normalize_category(category))
```

When both filters exist, `" AND ".join(conditions)` produces this query shape:

```sql
SELECT * FROM expenses
WHERE substr(spent_on,1,7)=? AND category=?
ORDER BY spent_on DESC,id DESC
```

The month and category never get inserted into the SQL text. They remain separate
values in `parameters`, so SQLite treats them as data. Dynamic query construction
is safe here because the possible SQL fragments are written by the program, not
provided by the user.

### Execution trace: combined month and category filter

For `list --month 2026-10 --category " FOOD "`:

1. `argparse` stores the month and category strings.
2. `main()` calls `store.list(args.month, args.category)`.
3. `valid_month()` returns `"2026-10"` after checking its shape and calendar.
4. `normalize_category()` trims and lowercases `" FOOD "` to `"food"`.
5. `list()` joins the two fixed conditions with `AND`.
6. SQLite receives the fixed query and the separate parameter list
   `["2026-10", "food"]`.
7. Only October rows whose stored category is exactly `food` are returned, still
   ordered by newest date and ID first.

An empty category is invalid rather than meaning “all categories.” Omitting the
flag produces `None`, which means no category condition. This makes accidental
empty input visible and keeps the meaning of omission distinct from invalid data.

### Design decision

The feature uses exact normalized matching, not substring or fuzzy search. Stored
categories already use `normalize_category()`, so applying the same function to a
filter makes `Food`, ` food `, and `FOOD` equivalent without adding a second set of
rules. Reusing `list()` from `summary()` and `export()` also prevents three query
implementations from drifting apart.

## 9. What changed in Version 1.4.2

Version 1.4.2 closes a CSV syntax gap in the atomic importer. Python's CSV reader
is permissive by default. For example, a final field that starts with `"` but
never closes can be returned as text instead of being rejected. That can hide a
damaged file and import data different from what the author intended.

### Strict parsing and the public error contract

`ExpenseStore.import_csv()` now constructs its reader with strict mode:

```python
reader = csv.DictReader(handle, strict=True)
```

Strict mode makes malformed quote structure raise `csv.Error`. The storage method
catches that parser-specific exception and converts it to the same `ValueError`
family already used for invalid amounts, dates, categories, notes, and row shapes:

```python
except csv.Error as exc:
    line_number = reader.reader.line_num or reader.line_num or 1
    raise ValueError(
        f"CSV line {line_number}: malformed CSV: {exc}."
    ) from exc
```

The CLI already catches `ValueError`, so users receive a normal command error and
exit status 2 instead of a raw Python traceback. `from exc` preserves the original
`csv.Error` as the exception cause for debugging.

### Why two line counters appear

`DictReader` wraps a lower-level CSV reader. After a successful row,
`reader.line_num` contains its physical line number. If parsing fails inside the
wrapped reader, `DictReader` may not get far enough to copy the new number to its
own property. `reader.reader.line_num` therefore supplies the current physical
line during a parser failure. The fallbacks still produce line 1 for an unusual
error before either reader has counted input.

This is intentionally a physical line number, not merely “record 2.” A quoted
field is allowed to span multiple physical lines, so the distinction matters when
someone opens the CSV in a text editor to repair it.

### Failure trace: unclosed quoted field

Assume the file contains a valid header, a valid expense on line 2, and this line:

```text
20,data,2026-10-02,"unfinished note
```

1. The line-2 expense is validated and stored only as a tuple in `records`.
2. The strict reader starts line 3, sees the opening quote, and reaches the end of
   the file without a closing quote.
3. The CSV module raises `csv.Error("unexpected end of data")`.
4. `import_csv()` reports `CSV line 3: malformed CSV: unexpected end of data.`
5. Execution leaves the file-reading phase before `self.connect()` or
   `executemany()` is reached.
6. The regression test proves the destination still contains only the row that
   existed before import; even the valid CSV row on line 2 was not inserted.

### Design decision

The parser error is handled inside `import_csv()` rather than in the CLI. That
keeps the storage API safe for terminal commands, tests, and a future HTTP API.
Strict syntax checking complements the existing semantic checks: the CSV reader
checks structure, while functions such as `money_to_kobo()` and `valid_date()`
check what each field means.

## 10. What changed in Version 1.4.1

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

## 11. What changed in Version 1.4

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

## 12. What changed in Version 1.3

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

## 13. What changed in Version 1.2

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

## 14. What changed in Version 1.1

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

## 15. Execution trace: `show 1`

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

## 16. Trace an added expense

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

## 17. Core Python functions and decisions

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

## 18. Classes, state, and SQLite

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

## 19. Tests and verified behavior

Run:

```sh
python -m unittest discover -s tests -v
```

The 2026-10-21 milestone run reported:

```text
Ran 30 tests
OK
```

Tests use a fresh temporary folder and database for each test. They cover exact
money conversion, rejected money and dates, exact 50/51-character category and
500/501-character note boundaries, persistence after reopening, sorting, normalized
category filtering, combined month/category filtering, filtered totals and CSV,
singular/plural formatting at counts 0, 1, and 2,
single-record lookup, valid partial updates, rejected updates, missing update IDs,
note clearing, SQL-looking text, CSV escaping, deletion,
confirmation, rejected deletion IDs with row preservation, export-to-import
behavior, fresh imported IDs, atomic rejection of an invalid later value,
malformed CSV shapes and quote syntax, snapshot independence, refresh of an
existing backup, same-path backup rejection, filtered JSON output, exact money
strings, literal UTF-8 text, and real CLI paths.

A passing suite proves only the listed cases passed in that environment. It does
not prove the absence of every bug, production performance, or security readiness.

## 20. Current limitations

- Single local user; no accounts, authentication, or per-user authorization.
- NGN only; the schema cannot safely mix currencies.
- No duplicate detection, undo, or audit history. Importing the same file twice
  creates two sets of expenses.
- Category filtering is an exact normalized match. There is no partial, fuzzy, or
  multi-category search.
- CSV import requires one of two exact header orders, generates fresh IDs, and
  holds every prepared row in memory before inserting.
- Formula-like text protected by export begins with an apostrophe. Import treats
  that apostrophe as literal data because removing it would be ambiguous.
- No schema migration tool.
- Text limits use Python's `len()` after trimming. There is no Unicode
  normalization or separate UTF-8 byte limit.
- No encryption; anyone who can read the database file can read its contents.
- Backups are manual, local, whole-database snapshots. There is no automatic
  schedule, rotation, encryption, remote upload, restore command, or record-level
  undo. Refreshing a named destination replaces its previous snapshot state.
- A backup needs enough writable local storage for another database copy.
- CSV export overwrites the target path.
- JSON export overwrites the target path, writes the selected rows in memory as
  one array, and has no matching JSON import. `amount_ngn` is intentionally a
  string rather than a JSON number.
- A valid confirmed deletion is immediate and has no undo or audit record.
- No API, browser interface, PostgreSQL, Docker, monitoring, or cloud deployment.
- No measured production users, reliability, load, or business impact.

These are scope boundaries, not hidden completed features.

## 21. Interview questions and honest answers

**What does serialization mean here?**
It means converting an internal `sqlite3.Row` into ordinary Python values with a
documented public shape, then encoding that list of values as JSON text.

**Why add `expense_to_dict()` instead of passing `sqlite3.Row` to `json.dump()`?**
The row object is database-specific and not directly part of JSON's supported
types. The mapping also deliberately chooses public names and money formatting.

**Why is `amount_ngn` a string instead of a JSON number?**
The app stores exact integer kobo. A two-decimal string preserves that exact
contract without introducing binary floating-point conversion.

**Why use one JSON array rather than write one object at a time?**
The exported selection is one collection and must be one valid JSON document.
Repeated independent `json.dump()` calls would concatenate values without an
array structure.

**What do `ensure_ascii=False` and `indent=2` change?**
The first keeps normal Unicode characters readable in the UTF-8 file. The second
adds predictable whitespace so people can inspect nested data easily.

**Why does JSON export call `list()`?**
It reuses month/category validation, normalized matching, safe SQL parameters,
ordering, and all existing filter tests instead of creating a competing query.

**Can FastAPI use this file-writing method directly?**
The row-to-dictionary mapping is reusable, but a web route would normally return
data for the framework to encode rather than write a local JSON file. HTTP behavior
still needs separate request/response models, tests, errors, and authorization.

**Why use `Connection.backup()` instead of an ordinary file copy?**
It asks SQLite to produce a consistent database snapshot through database
connections, including while the source may be accessed. An ordinary byte copy
does not express that database-level guarantee.

**Why compare resolved paths before opening the target?**
Different text can identify the same file. Resolving catches equivalent spellings
and stops the method from trying to use the live database as its own destination.

**Why create the destination's parent folder inside the method?**
The storage operation owns its complete path requirement. Callers can request a
nested destination without separately coordinating directory creation.

**What is the difference between the transaction context and `close()`?**
`with target:` commits successful work or rolls back on failure. `close()` releases
the connection resource. The method uses `finally` so closure happens on both
success and error paths.

**Why return a `Path` rather than print inside `backup()`?**
Returning keeps the storage layer independent from terminal presentation. The CLI
can print it, a test can compare it, and a future API can serialize it differently.

**Is the backup a live mirror?**
No. It is a snapshot of the source at one operation. Later source changes leave
that snapshot unchanged until the backup command is run again.

**Does this provide undo for one deleted expense?**
No. The snapshot contains the full database. This version has no merge or
record-level restore command; the backup can be inspected by passing it to `--db`.

**What is `format_expense_count()`?**
It is a small pure formatting function. It receives an integer count, chooses a
singular or plural label, and returns a string without printing or changing state.

**What is the conditional expression doing?**
`"expense" if count == 1 else "expenses"` selects one of two strings. Only the
exact value `1` is singular; zero and all other counts use the plural.

**Why return a string instead of printing inside the helper?**
Returning keeps the function reusable and simple to test. The command-line layer
decides whether and how to print the returned text.

**Why keep this helper out of `ExpenseStore`?**
The storage layer should return data, here an integer count. English grammar is a
presentation concern and belongs in the command-line module.

**Why test 0, 1, and 2?**
They cover the value before the singular case, the singular case itself, and the
first plural value after it. Together they catch the visible boundary bug.

**Why build the optional filters as condition and parameter lists?**
The method can support no filter, either individual filter, or both without four
duplicated SQL statements. The structure also keeps SQL text separate from values.

**Why is the dynamic query still parameterized?**
Only hard-coded fragments such as `category=?` are joined into the query. Month and
category values stay in the parameter list, so user input cannot become SQL syntax.

**Why normalize the category filter?**
Categories are normalized before storage. Reusing the same function gives filters
the same validation and makes differences in case or surrounding spaces irrelevant.

**Why do `summary()` and `export()` call `list()`?**
There is one selection rule to test and maintain. A filter fix in `list()` then
applies to displaying, totaling, and exporting records consistently.

**Why does an empty category fail instead of selecting every category?**
Omitting `--category` already means no category filter. Treating an empty supplied
value as invalid catches mistakes instead of silently broadening the result.

**Why enable strict CSV parsing?**
Permissive parsing can turn broken quote syntax into unexpected text. Strict mode
fails visibly, letting the user repair the file instead of silently importing it.

**Why catch `csv.Error` and raise `ValueError`?**
`csv.Error` describes the low-level parser. `ValueError` is the storage method's
existing invalid-input contract, which the CLI already converts into a clear
command error. Exception chaining retains the technical cause.

**Why read the underlying reader's line number after a parser failure?**
The wrapper updates its own counter only after a row succeeds. A failure can occur
first, while the underlying reader has already reached the bad physical line.

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

## 22. Hands-on exercises

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

### Exercise H — Break and repair a CSV

Create a four-column CSV with one valid row and a second row whose note begins with
a quote but never closes. Predict the error line, run `import`, and prove `list`
contains no imported rows. Add the closing quote, import again, and explain why
both rows now commit together.

### Exercise I — Trace combined filters

Add `food` and `data` expenses in two different months. Before running anything,
predict the rows and total for `summary --month 2026-10 --category food`. Run the
command, export the same filtered selection, inspect the CSV, then explain which
parts of the query are fixed SQL and which values are parameters.

### Exercise J — Predict the returned string

Without running the code, write the return value of `format_expense_count()` for
`0`, `1`, `2`, and `10`. Then call the function in a Python shell and compare your
answers. Temporarily change `count == 1` to `count > 0`, run the focused formatter
test, explain why it fails, restore the condition, and return the full suite to green.

### Exercise K — Prove snapshot independence

Create `live.db` with one expense, then run `backup snapshot.db`. Update or delete
the live row and predict what each database will show. Run `show 1` once with
`--db live.db` and once with `--db snapshot.db`. Explain the difference between a
snapshot and a live reference, then run backup again and confirm when the
destination changes. Finally, attempt to back up `live.db` onto itself and explain
why validation happens before the target connection opens.

### Exercise L — Trace Python data into JSON

Add food and data expenses containing a naira symbol, export only October food,
and inspect the file with `python -m json.tool`. Before opening it, predict the
Python type and JSON type of every field. Explain why the ID is a number but
`amount_ngn` is text. Temporarily remove `ensure_ascii=False`, observe how the
Unicode text changes without changing its decoded value, restore the argument,
and return all tests to green.

## 23. Readiness check

You understand Version 1.7 when you can trace a filtered `sqlite3.Row` through
`expense_to_dict()`, a list comprehension, `json.dump()`, and the final file;
predict every Python and JSON type; justify exact money text and readable UTF-8;
explain why the mapping can help a future API without claiming that API exists;
break and restore one encoder option; and return all 30 tests to green.
