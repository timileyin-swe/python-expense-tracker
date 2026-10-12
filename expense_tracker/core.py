"""Validation and SQLite persistence; money is stored as integer kobo."""
import csv
from contextlib import contextmanager
import re
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

MAX_KOBO = 1_000_000_000_000


def money_to_kobo(value):
    """Convert a positive decimal string without silently rounding money."""
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Amount must be a number.") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Amount must be finite and greater than zero.")
    if amount > Decimal(MAX_KOBO) / 100:
        raise ValueError("Amount exceeds the supported limit.")
    kobo = amount * 100
    if kobo != kobo.to_integral_value():
        raise ValueError("Amount must have at most two decimal places.")
    return int(kobo)


def format_money(kobo):
    return f"NGN {Decimal(kobo) / 100:,.2f}"


def valid_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Date must be YYYY-MM-DD.")
    date.fromisoformat(value)
    return value


def valid_month(value):
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise ValueError("Month must be YYYY-MM.")
    date.fromisoformat(value + "-01")
    return value


def csv_safe(value):
    """Neutralize spreadsheet formulas in user-controlled text fields."""
    if value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


class ExpenseStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                amount_kobo INTEGER NOT NULL CHECK(amount_kobo > 0),
                category TEXT NOT NULL,
                spent_on TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT ''
            )""")

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def add(self, amount, category, spent_on, note=""):
        kobo = money_to_kobo(amount)
        spent_on = valid_date(spent_on)
        category = category.strip().lower()
        note = note.strip()
        if not category or len(category) > 50:
            raise ValueError("Category must contain 1 to 50 characters.")
        if len(note) > 500:
            raise ValueError("Note must contain at most 500 characters.")
        with self.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO expenses(amount_kobo,category,spent_on,note) VALUES(?,?,?,?)",
                (kobo, category, spent_on, note),
            )
            return cursor.lastrowid

    def list(self, month=None):
        if month is not None:
            valid_month(month)
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM expenses" +
                (" WHERE substr(spent_on,1,7)=?" if month else "") +
                " ORDER BY spent_on DESC,id DESC",
                (month,) if month else (),
            ).fetchall()

    def summary(self, month=None):
        totals = {}
        for row in self.list(month):
            category = row["category"]
            totals[category] = totals.get(category, 0) + row["amount_kobo"]
        return dict(sorted(totals.items()))

    def delete(self, expense_id):
        with self.connect() as conn:
            cursor = conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
            return cursor.rowcount > 0

    def export(self, path, month=None):
        rows = self.list(month)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["id", "amount_ngn", "category", "date", "note"])
            for row in rows:
                writer.writerow([
                    row["id"], f"{Decimal(row['amount_kobo']) / 100:.2f}",
                    csv_safe(row["category"]), row["spent_on"], csv_safe(row["note"]),
                ])
        return len(rows)
