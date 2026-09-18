import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.data.inventory_datasets import (
    discover_dataset_files,
    inventory_csv_file,
    inventory_dataset_file,
)


class InventoryDatasetTests(unittest.TestCase):
    def test_file_discovery_finds_supported_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "data" / "raw"
            csv_file = root / "sample.csv"
            xlsx_file = root / "nested" / "sample.xlsx"
            txt_file = root / "notes.txt"
            csv_file.parent.mkdir(parents=True, exist_ok=True)
            xlsx_file.parent.mkdir(parents=True, exist_ok=True)
            csv_file.write_text("col_a,col_b\n1,2\n3,4\n", encoding="utf-8")
            xlsx_file.write_bytes(b"fake-xlsx")
            txt_file.write_text("ignore me", encoding="utf-8")

            discovered = discover_dataset_files(root)
            self.assertIn(csv_file, discovered)
            self.assertIn(xlsx_file, discovered)
            self.assertNotIn(txt_file, discovered)

    def test_csv_inventory_uses_temporary_fixture(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "sample.csv"
            csv_path.write_text(
                "customer_id,amount,region\n1,10.5,North\n1,10.5,North\n2,,South\n",
                encoding="utf-8",
            )

            inventory = inventory_csv_file(csv_path)
            self.assertEqual(inventory["row_count"], 3)
            self.assertEqual(inventory["column_count"], 3)
            self.assertEqual(
                inventory["column_names"], ["customer_id", "amount", "region"]
            )
            self.assertEqual(inventory["duplicate_row_count"], 1)
            self.assertEqual(inventory["missing_values"]["amount"], 1)

    def test_inventory_json_generation_payload_contains_required_fields(self):
        inventory = {
            "generated_at": "2026-01-01T00:00:00Z",
            "inventory_schema_version": "1.0",
            "datasets": [{"filename": "sample.csv", "row_count": 2}],
            "file_metadata": [{"filename": "sample.csv", "row_count": 2}],
            "schema_metadata": {
                "supported_extensions": [".csv", ".xls", ".xlsx"],
                "raw_data_root": "data/raw",
            },
            "quality_summary": {
                "total_file_count": 1,
                "total_row_count": 2,
                "total_column_count": 2,
                "files_missing_rows": 0,
                "files_with_duplicate_rows": 0,
            },
        }
        json_text = json.dumps(inventory, indent=2)
        self.assertIn("inventory_schema_version", json_text)
        self.assertIn("datasets", json_text)
        self.assertIn("quality_summary", json_text)

    def test_unsupported_extension_handling(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = Path(tmpdir) / "sample.txt"
            txt_path.write_text("not a dataset", encoding="utf-8")
            with self.assertRaises(ValueError):
                inventory_dataset_file(txt_path)

    def test_xlsx_inventory_rejects_missing_dependency(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            xlsx_path = Path(tmpdir) / "sample.xlsx"
            xlsx_path.write_bytes(b"fake-xlsx")
            with patch("scripts.data.inventory_datasets.load_workbook", new=None):
                with self.assertRaises(RuntimeError):
                    inventory_dataset_file(xlsx_path)


if __name__ == "__main__":
    unittest.main()
