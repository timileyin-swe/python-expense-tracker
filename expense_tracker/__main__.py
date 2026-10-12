"""Run with python -m expense_tracker."""
import argparse
import sqlite3
from datetime import date
from pathlib import Path
from .core import ExpenseStore, format_money


def main(argv=None):
    parser = argparse.ArgumentParser(description="Track personal expenses in NGN.")
    parser.add_argument("--db", default=str(Path.home() / ".expense-tracker" / "expenses.db"))
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="Record an expense")
    add.add_argument("amount")
    add.add_argument("category")
    add.add_argument("--date", default=date.today().isoformat())
    add.add_argument("--note", default="")
    for name in ("list", "summary", "export"):
        command = commands.add_parser(name)
        command.add_argument("--month", help="Filter using YYYY-MM")
        if name == "export":
            command.add_argument("path")
    delete = commands.add_parser("delete")
    delete.add_argument("id", type=int)
    delete.add_argument("--yes", action="store_true", help="Confirm permanent deletion")
    args = parser.parse_args(argv)
    try:
        store = ExpenseStore(args.db)
        if args.command == "add":
            record_id = store.add(args.amount, args.category, args.date, args.note)
            print(f"Added expense #{record_id}.")
        elif args.command == "list":
            rows = store.list(args.month)
            if not rows:
                print("No expenses found.")
            for row in rows:
                print(f"#{row['id']} | {row['spent_on']} | {format_money(row['amount_kobo'])} | {row['category']} | {row['note']}")
        elif args.command == "summary":
            totals = store.summary(args.month)
            for category, kobo in totals.items():
                print(f"{category}: {format_money(kobo)}")
            print(f"TOTAL: {format_money(sum(totals.values()))}")
        elif args.command == "export":
            print(f"Exported {store.export(args.path, args.month)} expenses.")
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
