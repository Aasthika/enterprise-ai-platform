import datetime
import json
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from scripts.data.profile_datasets import (
    discover_dataset_files,
    profile_dataset_file,
    generate_profile_payload,
)


class ProfileDatasetsTests(unittest.TestCase):
    def test_discovery_finds_supported_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "data" / "raw"
            xlsx_file = root / "nested" / "sample.xlsx"
            csv_file = root / "sample.csv"
            txt_file = root / "notes.txt"
            xlsx_file.parent.mkdir(parents=True, exist_ok=True)
            csv_file.parent.mkdir(parents=True, exist_ok=True)

            xlsx_file.write_bytes(b"fake-xlsx")
            csv_file.write_text("id,value\n1,2\n", encoding="utf-8")
            txt_file.write_text("ignore", encoding="utf-8")

            discovered = discover_dataset_files(root)
            self.assertIn(xlsx_file, discovered)
            self.assertIn(csv_file, discovered)
            self.assertNotIn(txt_file, discovered)

    def test_tiny_workbook_profiling(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook_path = Path(tmpdir) / "tiny.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.title = "Sales"
            ws.append(["Customer", "Quantity", "Price", "OrderDate", "Notes"])
            ws.append(["A", 10, 5.5, "2024-01-01", ""])
            ws.append(["A", 10, 5.5, "2024-01-01", ""])
            ws.append(["B", -1, 0, "2024-02-30", "review"])
            ws.append(["C", 0, -2.5, "2024-03-01", None])
            wb.save(workbook_path)
            wb.close()

            profile = profile_dataset_file(workbook_path)
            self.assertEqual(profile["filename"], "tiny.xlsx")
            self.assertEqual(profile["sheet_names"], ["Sales"])
            self.assertEqual(profile["sheet_count"], 1)
            self.assertEqual(profile["sheets"][0]["row_count"], 4)
            self.assertEqual(profile["sheets"][0]["column_count"], 5)
            self.assertEqual(
                [col["name"] for col in profile["sheets"][0]["columns"]],
                ["Customer", "Quantity", "Price", "OrderDate", "Notes"],
            )
            quantity = next(
                col
                for col in profile["sheets"][0]["columns"]
                if col["name"] == "Quantity"
            )
            self.assertEqual(quantity["inferred_type"], "numeric")
            self.assertEqual(quantity["missing_count"], 0)
            self.assertIn("numeric_summary", quantity)
            self.assertEqual(profile["quality_checks"]["duplicate_rows"], 1)
            self.assertNotIn("_raw_rows", json.dumps(profile, ensure_ascii=False))
            self.assertLessEqual(
                len(profile["quality_checks"]["negative_quantities"]["sample"]),
                10,
            )
            self.assertLessEqual(
                len(profile["quality_checks"]["negative_prices"]["sample"]),
                10,
            )

    def test_type_inference_and_missing_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook_path = Path(tmpdir) / "types.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.title = "Data"
            ws.append(["TextCol", "NumericCol", "DateCol", "MixedCol", "EmptyCol"])
            ws.append(["alpha", 1, "2024-01-01", "1", None])
            ws.append(["beta", 2, "2024-01-02", "two", None])
            ws.append([None, 3, "2024-01-03", "3", None])
            wb.save(workbook_path)
            wb.close()

            profile = profile_dataset_file(workbook_path)
            text_col = next(
                col
                for col in profile["sheets"][0]["columns"]
                if col["name"] == "TextCol"
            )
            numeric_col = next(
                col
                for col in profile["sheets"][0]["columns"]
                if col["name"] == "NumericCol"
            )
            date_col = next(
                col
                for col in profile["sheets"][0]["columns"]
                if col["name"] == "DateCol"
            )
            mixed_col = next(
                col
                for col in profile["sheets"][0]["columns"]
                if col["name"] == "MixedCol"
            )
            empty_col = next(
                col
                for col in profile["sheets"][0]["columns"]
                if col["name"] == "EmptyCol"
            )

            self.assertEqual(text_col["inferred_type"], "text")
            self.assertEqual(numeric_col["inferred_type"], "numeric")
            self.assertEqual(date_col["inferred_type"], "date-like")
            self.assertEqual(mixed_col["inferred_type"], "mixed")
            self.assertEqual(empty_col["inferred_type"], "empty")
            self.assertEqual(text_col["missing_count"], 1)
            self.assertEqual(empty_col["missing_count"], 3)
            self.assertEqual(empty_col["missing_percentage"], 100.0)

    def test_invoice_date_metrics_are_calculated_directly_and_never_exceed_non_empty_count(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook_path = Path(tmpdir) / "dates.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.title = "Invoices"
            ws.append(["InvoiceDate", "OtherDate", "Quantity"])
            ws.append(["2024-01-01", "2024-02-01", 1])
            ws.append(["bad-date", "2024-03-01", 2])
            ws.append([None, "2024-04-01", 3])
            ws.append(["2024-02-29", "2024-05-01", 4])
            ws.append([datetime.date(2024, 3, 1), "bad-date", 5])
            wb.save(workbook_path)
            wb.close()

            profile = profile_dataset_file(workbook_path)
            sheet = profile["sheets"][0]
            invoice_metrics = sheet["invoice_date_metrics"]
            date_issues = profile["quality_checks"]["date_parsing_issues"]

            self.assertEqual(invoice_metrics["non_empty_count"], 4)
            self.assertEqual(invoice_metrics["valid_date_count"], 3)
            self.assertEqual(invoice_metrics["invalid_date_count"], 1)
            self.assertEqual(len(invoice_metrics["date_parsing_issues"]), 1)
            self.assertLessEqual(
                len(invoice_metrics["date_parsing_issues"]),
                invoice_metrics["non_empty_count"],
            )
            self.assertEqual(len(date_issues), 1)
            self.assertEqual(date_issues[0]["column"], "InvoiceDate")
            self.assertEqual(date_issues[0]["value"], "bad-date")
            self.assertNotIn("_raw_rows", json.dumps(profile, ensure_ascii=False))

    def test_datetime_objects_are_valid_and_only_invoice_date_counts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook_path = Path(tmpdir) / "datetimes.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.title = "Dates"
            ws.append(["InvoiceDate", "OtherDate", "Quantity"])
            ws.append(["2024-01-01", "2024-02-01", 1])
            ws.append(["bad-date", "2024-03-01", 2])
            ws.append([None, "2024-04-01", 3])
            wb.save(workbook_path)
            wb.close()

            profile = profile_dataset_file(workbook_path)
            date_issues = profile["quality_checks"]["date_parsing_issues"]
            other_issue_values = [
                issue["value"]
                for issue in date_issues
                if issue["column"] == "OtherDate"
            ]

            self.assertEqual(len(date_issues), 1)
            self.assertEqual(date_issues[0]["column"], "InvoiceDate")
            self.assertEqual(date_issues[0]["value"], "bad-date")
            self.assertEqual(other_issue_values, [])
            self.assertLessEqual(
                len(profile["quality_checks"]["date_parsing_issues"]), 10
            )

    def test_numeric_statistics_and_json_generation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook_path = Path(tmpdir) / "stats.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.title = "Stats"
            ws.append(["Quantity", "Price"])
            ws.append([10, 5.5])
            ws.append([20, 7.25])
            ws.append([30, 10])
            wb.save(workbook_path)
            wb.close()

            profile = profile_dataset_file(workbook_path)
            quantity = next(
                col
                for col in profile["sheets"][0]["columns"]
                if col["name"] == "Quantity"
            )
            price = next(
                col for col in profile["sheets"][0]["columns"] if col["name"] == "Price"
            )
            self.assertEqual(quantity["numeric_summary"]["min"], 10)
            self.assertEqual(quantity["numeric_summary"]["max"], 30)
            self.assertEqual(quantity["numeric_summary"]["mean"], 20)
            self.assertEqual(price["numeric_summary"]["min"], 5.5)
            self.assertEqual(price["numeric_summary"]["max"], 10)

            payload = generate_profile_payload(profile)
            json_text = json.dumps(payload, indent=2)
            self.assertIn("generated_at", json_text)
            self.assertIn("datasets", json_text)
            self.assertIn("quality_summary", json_text)
            self.assertNotIn("_raw_rows", json_text)
            self.assertNotIn("every row", json_text.lower())
            self.assertLessEqual(
                len(profile["quality_checks"]["zero_prices"]["sample"]),
                10,
            )

    def test_unsupported_extension_handling(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = Path(tmpdir) / "sample.txt"
            txt_path.write_text("not a dataset", encoding="utf-8")
            with self.assertRaises(ValueError):
                profile_dataset_file(txt_path)


if __name__ == "__main__":
    unittest.main()
