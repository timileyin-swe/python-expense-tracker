import csv
import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from expense_tracker.core import ExpenseStore, money_to_kobo
from expense_tracker.__main__ import format_expense_count, main


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "expenses.db"
        self.store = ExpenseStore(self.db)

    def test_exact_money(self):
        self.assertEqual(money_to_kobo("0.29"), 29)
        self.assertEqual(money_to_kobo("1000.50"), 100050)

    def test_format_expense_count(self):
        self.assertEqual(format_expense_count(0), "0 expenses")
        self.assertEqual(format_expense_count(1), "1 expense")
        self.assertEqual(format_expense_count(2), "2 expenses")

    def test_invalid_money(self):
        for value in ("0", "-1", "nan", "Infinity", "abc", "1.001", "1e100"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                money_to_kobo(value)

    def test_validation(self):
        for category, day in (("", "2026-10-12"), ("food", "2026-02-30"), ("food", "20261012")):
            with self.subTest(category=category, day=day), self.assertRaises(ValueError):
                self.store.add("1", category, day)
        self.assertEqual(len(self.store.list()), 0)

    def test_category_length_boundaries(self):
        maximum_category = "A" * 50
        record_id = self.store.add("1", f" {maximum_category} ", "2026-10-13")
        self.assertEqual(self.store.get(record_id)["category"], "a" * 50)
        with self.assertRaisesRegex(ValueError, "1 to 50 characters"):
            self.store.add("1", "b" * 51, "2026-10-13")
        self.assertEqual(len(self.store.list()), 1)

    def test_note_length_boundaries(self):
        maximum_note = "N" * 500
        record_id = self.store.add("1", "study", "2026-10-13", f" {maximum_note} ")
        self.assertEqual(self.store.get(record_id)["note"], maximum_note)
        with self.assertRaisesRegex(ValueError, "at most 500 characters"):
            self.store.add("1", "study", "2026-10-13", "n" * 501)
        self.assertEqual(len(self.store.list()), 1)

    def test_persistence_and_summary(self):
        self.store.add("0.10", " Food ", "2026-10-01")
        self.store.add("0.20", "food", "2026-10-02")
        self.store.add("50", "transport", "2026-09-01")
        reopened = ExpenseStore(self.db)
        self.assertEqual(reopened.summary("2026-10"), {"food": 30})
        self.assertEqual(len(reopened.list()), 3)
        self.assertEqual(reopened.list()[0]["spent_on"], "2026-10-02")

    def test_category_filter_normalizes_and_combines_with_month(self):
        october_food = self.store.add("10", " Food ", "2026-10-02", "Lunch")
        self.store.add("20", "food", "2026-09-30", "Breakfast")
        self.store.add("30", "data", "2026-10-03", "Weekly plan")

        rows = self.store.list(month="2026-10", category=" FOOD ")
        self.assertEqual([row["id"] for row in rows], [october_food])
        self.assertEqual(self.store.summary(category="Food"), {"food": 3000})

        path = Path(self.temp.name) / "food-october.csv"
        self.assertEqual(
            self.store.export(path, month="2026-10", category="food"), 1
        )
        with path.open(newline="", encoding="utf-8") as handle:
            exported = list(csv.DictReader(handle))
        self.assertEqual([row["note"] for row in exported], ["Lunch"])

        with self.assertRaisesRegex(ValueError, "1 to 50 characters"):
            self.store.list(category="   ")

    def test_get_existing_missing_and_invalid_id(self):
        record_id = self.store.add("25.50", "data", "2026-10-12", "Night plan")
        row = self.store.get(record_id)
        self.assertEqual(row["amount_kobo"], 2550)
        self.assertEqual(row["category"], "data")
        self.assertIsNone(self.store.get(record_id + 1))
        for invalid_id in (0, -1, True, "1"):
            with self.subTest(invalid_id=invalid_id), self.assertRaises(ValueError):
                self.store.get(invalid_id)

    def test_update_selected_fields_and_clear_note(self):
        record_id = self.store.add("25.50", "data", "2026-10-12", "Night plan")
        row = self.store.update(record_id, category=" Transport ", note="")
        self.assertEqual(row["amount_kobo"], 2550)
        self.assertEqual(row["category"], "transport")
        self.assertEqual(row["spent_on"], "2026-10-12")
        self.assertEqual(row["note"], "")
        row = self.store.update(record_id, amount="99.95", spent_on="2026-10-14")
        self.assertEqual(row["amount_kobo"], 9995)
        self.assertEqual(row["category"], "transport")
        self.assertEqual(row["spent_on"], "2026-10-14")
        self.assertEqual(row["note"], "")

    def test_update_rejects_invalid_or_missing_changes(self):
        record_id = self.store.add("25.50", "data", "2026-10-12", "Night plan")
        original = dict(self.store.get(record_id))
        with self.assertRaisesRegex(ValueError, "at least one field"):
            self.store.update(record_id)
        invalid_changes = (
            {"amount": "0"},
            {"category": ""},
            {"spent_on": "2026-02-30"},
            {"note": "n" * 501},
        )
        for changes in invalid_changes:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.store.update(record_id, **changes)
        self.assertEqual(dict(self.store.get(record_id)), original)
        self.assertIsNone(self.store.update(record_id + 1, amount="10"))

    def test_invalid_month(self):
        for value in ("2026-13", "202610", "2026-1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.store.list(value)

    def test_sql_parameters_preserve_text(self):
        self.store.add("10", "food", "2026-10-01", "'); DROP TABLE expenses;--")
        self.assertEqual(len(self.store.list()), 1)

    def test_export_escaping_and_exact_amount(self):
        self.store.add("12.50", "food", "2026-10-01", '=SUM(1,2)')
        path = Path(self.temp.name) / "export.csv"
        self.assertEqual(self.store.export(path), 1)
        with path.open(newline="", encoding="utf-8") as handle:
            row = list(csv.DictReader(handle))[0]
        self.assertEqual(row["amount_ngn"], "12.50")
        self.assertEqual(row["note"], "'=SUM(1,2)")

    def test_import_exported_csv_uses_new_ids(self):
        source = ExpenseStore(Path(self.temp.name) / "source.db")
        source.add("12.50", "Food", "2026-10-01", "Lunch")
        source.add("20", "data", "2026-10-02", "Weekly plan")
        path = Path(self.temp.name) / "export.csv"
        source.export(path)

        existing_id = self.store.add("5", "transport", "2026-09-30")
        self.assertEqual(self.store.import_csv(path), 2)

        self.assertEqual(existing_id, 1)
        self.assertEqual([row["id"] for row in self.store.list()], [2, 3, 1])
        self.assertEqual(self.store.get(2)["category"], "data")
        self.assertEqual(self.store.get(3)["amount_kobo"], 1250)
        self.assertEqual(self.store.get(3)["note"], "Lunch")

    def test_import_is_atomic_and_reports_invalid_line(self):
        existing_id = self.store.add("5", "transport", "2026-09-30")
        path = Path(self.temp.name) / "invalid.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["amount_ngn", "category", "date", "note"])
            writer.writerow(["12.50", "food", "2026-10-01", "Lunch"])
            writer.writerow(["0", "data", "2026-10-02", "Invalid amount"])

        with self.assertRaisesRegex(ValueError, r"CSV line 3:.*greater than zero"):
            self.store.import_csv(path)
        self.assertEqual([row["id"] for row in self.store.list()], [existing_id])

    def test_import_rejects_bad_header_and_extra_fields(self):
        path = Path(self.temp.name) / "invalid-shape.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["amount", "category", "date", "note"])
        with self.assertRaisesRegex(ValueError, "CSV header must be"):
            self.store.import_csv(path)

        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["amount_ngn", "category", "date", "note"])
            writer.writerow(["12.50", "food", "2026-10-01", "Lunch", "unexpected"])
        with self.assertRaisesRegex(ValueError, "CSV line 2: expected exactly 4 fields"):
            self.store.import_csv(path)
        self.assertEqual(self.store.list(), [])

    def test_import_rejects_malformed_quotes_atomically(self):
        existing_id = self.store.add("5", "transport", "2026-09-30")
        path = Path(self.temp.name) / "malformed.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write("amount_ngn,category,date,note\n")
            handle.write("12.50,food,2026-10-01,Lunch\n")
            handle.write('20,data,2026-10-02,"unfinished note\n')

        with self.assertRaisesRegex(ValueError, "CSV line 3: malformed CSV"):
            self.store.import_csv(path)
        self.assertEqual([row["id"] for row in self.store.list()], [existing_id])

    def test_delete_and_missing_record(self):
        record_id = self.store.add("10", "food", "2026-10-01")
        self.assertTrue(self.store.delete(record_id))
        self.assertFalse(self.store.delete(record_id))

    def test_delete_rejects_invalid_ids_without_removing_a_row(self):
        record_id = self.store.add("10", "food", "2026-10-01")
        for invalid_id in (0, -1, True, "1"):
            with self.subTest(invalid_id=invalid_id), self.assertRaisesRegex(
                ValueError, "positive integer"
            ):
                self.store.delete(invalid_id)
        self.assertIsNotNone(self.store.get(record_id))

    def test_cli_requires_delete_confirmation(self):
        record_id = self.store.add("10", "food", "2026-10-01")
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
            main(["--db", str(self.db), "delete", str(record_id)])
        self.assertEqual(exc.exception.code, 2)
        self.assertEqual(len(self.store.list()), 1)

        error_output = io.StringIO()
        with redirect_stderr(error_output), self.assertRaises(SystemExit) as exc:
            main(["--db", str(self.db), "delete", "-1", "--yes"])
        self.assertEqual(exc.exception.code, 2)
        self.assertIn("Expense ID must be a positive integer.", error_output.getvalue())
        self.assertEqual(len(self.store.list()), 1)

    def test_cli_add_and_summary(self):
        output = io.StringIO()
        with redirect_stdout(output):
            main(["--db", str(self.db), "add", "1500", "food", "--date", "2026-10-12"])
            main(["--db", str(self.db), "summary", "--month", "2026-10"])
        self.assertIn("TOTAL: NGN 1,500.00", output.getvalue())

    def test_cli_category_filter_for_list_summary_and_export(self):
        food_id = self.store.add("1500", "food", "2026-10-12", "Lunch")
        self.store.add("700", "data", "2026-10-12", "Weekly plan")
        self.store.add("500", "food", "2026-09-30", "Breakfast")

        output = io.StringIO()
        with redirect_stdout(output):
            main([
                "--db", str(self.db), "list", "--month", "2026-10",
                "--category", " FOOD ",
            ])
        self.assertIn(f"#{food_id} | 2026-10-12 | NGN 1,500.00", output.getvalue())
        self.assertNotIn("data", output.getvalue())
        self.assertNotIn("Breakfast", output.getvalue())

        output = io.StringIO()
        with redirect_stdout(output):
            main(["--db", str(self.db), "summary", "--category", "food"])
        self.assertEqual(
            output.getvalue().strip(),
            "food: NGN 2,000.00\nTOTAL: NGN 2,000.00",
        )

        path = Path(self.temp.name) / "filtered.csv"
        output = io.StringIO()
        with redirect_stdout(output):
            main([
                "--db", str(self.db), "export", str(path),
                "--month", "2026-10", "--category", "food",
            ])
        self.assertEqual(output.getvalue().strip(), "Exported 1 expense.")
        with path.open(newline="", encoding="utf-8") as handle:
            exported = list(csv.DictReader(handle))
        self.assertEqual([row["note"] for row in exported], ["Lunch"])

    def test_cli_show_and_missing_id(self):
        record_id = self.store.add("1500", "food", "2026-10-12", "Lunch")
        output = io.StringIO()
        with redirect_stdout(output):
            main(["--db", str(self.db), "show", str(record_id)])
        self.assertEqual(
            output.getvalue().strip(),
            f"#{record_id} | 2026-10-12 | NGN 1,500.00 | food | Lunch",
        )
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
            main(["--db", str(self.db), "show", "999"])
        self.assertEqual(exc.exception.code, 2)

    def test_cli_update_and_missing_id(self):
        record_id = self.store.add("1500", "food", "2026-10-12", "Lunch")
        output = io.StringIO()
        with redirect_stdout(output):
            main([
                "--db", str(self.db), "update", str(record_id),
                "--amount", "2200.50", "--category", "Transport", "--note", "",
            ])
        self.assertEqual(
            output.getvalue().strip(),
            f"Updated #{record_id} | 2026-10-12 | NGN 2,200.50 | transport |",
        )
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
            main(["--db", str(self.db), "update", str(record_id)])
        self.assertEqual(exc.exception.code, 2)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
            main(["--db", str(self.db), "update", "999", "--amount", "10"])
        self.assertEqual(exc.exception.code, 2)

    def test_cli_import_without_id_column(self):
        path = Path(self.temp.name) / "import.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["amount_ngn", "category", "date", "note"])
            writer.writerow(["1500.25", " Food ", "2026-10-15", " Dinner "])
        output = io.StringIO()
        with redirect_stdout(output):
            main(["--db", str(self.db), "import", str(path)])
        self.assertEqual(output.getvalue().strip(), "Imported 1 expense.")
        row = self.store.list()[0]
        self.assertEqual(row["amount_kobo"], 150025)
        self.assertEqual(row["category"], "food")
        self.assertEqual(row["note"], "Dinner")


if __name__ == "__main__":
    unittest.main()
