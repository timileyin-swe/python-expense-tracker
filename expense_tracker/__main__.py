"""Run with python -m expense_tracker."""
import argparse
import sqlite3
from datetime import date
from pathlib import Path
from .core import ExpenseStore, format_money


def format_expense(row):
    """Build the single-line representation used by list, show, and update."""
    return (
        f"#{row['id']} | {row['spent_on']} | "
        f"{format_money(row['amount_kobo'])} | {row['category']} | {row['note']}"
    )


def format_expense_count(count):
    """Return a count with the grammatically correct expense label."""
    label = "expense" if count == 1 else "expenses"
    return f"{count} {label}"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Track personal expenses in NGN.")
    parser.add_argument(
        "--db",
        default=str(Path.home() / ".expense-tracker" / "expenses.db"),
        help="SQLite database path",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser(
        "add", help="Record an expense", description="Record one validated expense."
    )
    add.add_argument("amount", help="Positive NGN amount")
    add.add_argument("category", help="Expense category")
    add.add_argument(
        "--date", default=date.today().isoformat(), help="Date using YYYY-MM-DD"
    )
    add.add_argument("--note", default="", help="Optional expense note")
    show = commands.add_parser(
        "show", help="Show one expense by ID", description="Show one expense by ID."
    )
    show.add_argument("id", type=int, help="Positive expense ID")
    update = commands.add_parser(
        "update",
        help="Change selected fields on one expense",
        description="Change selected fields on one expense.",
    )
    update.add_argument("id", type=int, help="Positive expense ID")
    update.add_argument("--amount", help="New NGN amount")
    update.add_argument("--category", help="New category")
    update.add_argument("--date", dest="spent_on", help="New date using YYYY-MM-DD")
    update.add_argument("--note", help="New note; pass an empty string to clear it")
    filtered_commands = {
        "list": "List matching expenses",
        "summary": "Summarize matching expenses by category",
        "export": "Export matching expenses to CSV",
        "export-json": "Export matching expenses to JSON",
    }
    for name, help_text in filtered_commands.items():
        command = commands.add_parser(
            name, help=help_text, description=f"{help_text}."
        )
        command.add_argument("--month", help="Filter using YYYY-MM")
        command.add_argument("--category", help="Filter by exact category")
        if name in ("export", "export-json"):
            file_type = "CSV" if name == "export" else "JSON"
            command.add_argument("path", help=f"Destination {file_type} file")
    import_command = commands.add_parser(
        "import",
        help="Import expenses from CSV",
        description="Import validated expenses from a CSV file.",
    )
    import_command.add_argument("path", help="Source CSV file")
    backup = commands.add_parser(
        "backup",
        help="Create a consistent database backup",
        description="Create or refresh a consistent database backup.",
    )
    backup.add_argument("path", help="Destination SQLite database")
    delete = commands.add_parser(
        "delete",
        help="Permanently delete an expense",
        description="Permanently delete one expense after confirmation.",
    )
    delete.add_argument("id", type=int, help="Positive expense ID")
    delete.add_argument("--yes", action="store_true", help="Confirm permanent deletion")
    args = parser.parse_args(argv)
    try:
        store = ExpenseStore(args.db)
        if args.command == "add":
            record_id = store.add(args.amount, args.category, args.date, args.note)
            print(f"Added expense #{record_id}.")
        elif args.command == "show":
            row = store.get(args.id)
            if row is None:
                parser.error("Expense ID not found.")
            print(format_expense(row))
        elif args.command == "update":
            row = store.update(
                args.id,
                amount=args.amount,
                category=args.category,
                spent_on=args.spent_on,
                note=args.note,
            )
            if row is None:
                parser.error("Expense ID not found.")
            print(f"Updated {format_expense(row)}")
        elif args.command == "list":
            rows = store.list(args.month, args.category)
            if not rows:
                print("No expenses found.")
            for row in rows:
                print(format_expense(row))
        elif args.command == "summary":
            totals = store.summary(args.month, args.category)
            for category, kobo in totals.items():
                print(f"{category}: {format_money(kobo)}")
            print(f"TOTAL: {format_money(sum(totals.values()))}")
        elif args.command == "export":
            count = store.export(args.path, args.month, args.category)
            print(f"Exported {format_expense_count(count)}.")
        elif args.command == "export-json":
            count = store.export_json(args.path, args.month, args.category)
            print(f"Exported {format_expense_count(count)} to JSON.")
        elif args.command == "import":
            count = store.import_csv(args.path)
            print(f"Imported {format_expense_count(count)}.")
        elif args.command == "backup":
            path = store.backup(args.path)
            print(f"Backed up database to {path}.")
        elif args.command == "delete":
            if not args.yes:
                parser.error("Deletion requires --yes. Back up your database first.")
            if not store.delete(args.id):
                parser.error("Expense ID not found.")
            print(f"Deleted expense #{args.id}.")
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
