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
    parser.add_argument("--db", default=str(Path.home() / ".expense-tracker" / "expenses.db"))
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="Record an expense")
    add.add_argument("amount")
    add.add_argument("category")
    add.add_argument("--date", default=date.today().isoformat())
    add.add_argument("--note", default="")
    show = commands.add_parser("show", help="Show one expense by ID")
    show.add_argument("id", type=int)
    update = commands.add_parser("update", help="Change selected fields on one expense")
    update.add_argument("id", type=int)
    update.add_argument("--amount", help="New NGN amount")
    update.add_argument("--category", help="New category")
    update.add_argument("--date", dest="spent_on", help="New date using YYYY-MM-DD")
    update.add_argument("--note", help="New note; pass an empty string to clear it")
    for name in ("list", "summary", "export"):
        command = commands.add_parser(name)
        command.add_argument("--month", help="Filter using YYYY-MM")
        command.add_argument("--category", help="Filter by exact category")
        if name == "export":
            command.add_argument("path")
    import_command = commands.add_parser("import", help="Import expenses from CSV")
    import_command.add_argument("path")
    delete = commands.add_parser("delete")
    delete.add_argument("id", type=int)
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
        elif args.command == "import":
            count = store.import_csv(args.path)
            print(f"Imported {format_expense_count(count)}.")
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
