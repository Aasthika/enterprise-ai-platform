"""Inventory tool for dataset discovery and metadata collection.

This tool is intentionally read-only with respect to the project raw-data area. It
walks the data/raw directory, inspects supported file types, and records metadata in
data/metadata without modifying source datasets.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

RAW_DATA_DIR = Path("data/raw")
METADATA_DIR = Path("data/metadata")
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover - dependency is optional at runtime
    load_workbook = None

try:
    import xlrd
except ImportError:  # pragma: no cover - dependency is optional at runtime
    xlrd = None


def discover_dataset_files(root: Path) -> list[Path]:
    """Return supported dataset files found under the raw-data directory."""
    if not root.exists():
        raise FileNotFoundError(f"Raw data directory does not exist: {root}")

    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == ".gitkeep":
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return files


def find_unsupported_files(root: Path) -> list[Path]:
    """Return unsupported files under the raw-data tree for explicit reporting."""
    if not root.exists():
        return []

    unsupported: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == ".gitkeep":
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            unsupported.append(path)
    return unsupported


def safe_relative_path(path: Path) -> str:
    """Return a repo-relative path when possible, otherwise use the filename only."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError:
        return path.as_posix()


def infer_value_type(value: Any) -> str:
    """Infer a conservative data type from a scalar value."""
    if value is None:
        return "null"

    text = str(value).strip()
    if text == "":
        return "empty"
    if text.lower() in {"true", "false"}:
        return "bool"
    try:
        int(text)
        return "int"
    except ValueError:
        pass
    try:
        float(text)
        return "float"
    except ValueError:
        pass
    return "string"


def normalize_missing(value: Any) -> bool:
    """Return whether the provided value should be treated as missing."""
    if value is None:
        return True
    text = str(value).strip()
    return text.lower() in {"", "na", "n/a", "null", "none", "nan"}


def inventory_csv_file(path: Path) -> dict[str, Any]:
    """Inventory a CSV file without modifying the source dataset."""
    relative_path = safe_relative_path(path)
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            rows.append(row)

    if not rows:
        return {
            "relative_path": str(relative_path),
            "filename": path.name,
            "extension": path.suffix.lower(),
            "file_size_bytes": path.stat().st_size,
            "file_size_mb": round(path.stat().st_size / (1024 * 1024), 6),
            "row_count": 0,
            "column_count": 0,
            "column_names": [],
            "data_types": {},
            "missing_values": {},
            "duplicate_row_count": 0,
            "sheet_names": [],
            "sheet_details": [],
        }

    header = rows[0]
    data_rows = rows[1:]
    column_count = len(header)
    column_names = header

    inferred_types: dict[str, str] = {}
    missing_values: dict[str, int] = {name: 0 for name in header}
    seen_rows: set[tuple[str, ...]] = set()
    duplicate_rows = 0

    for row in data_rows:
        padded = row[:column_count] + [""] * max(0, column_count - len(row))
        seen_key = tuple(padded)
        if seen_key in seen_rows:
            duplicate_rows += 1
        else:
            seen_rows.add(seen_key)

        for index, value in enumerate(padded):
            column_name = header[index]
            if normalize_missing(value):
                missing_values[column_name] += 1

        for index, column_name in enumerate(header):
            if index >= len(padded):
                continue
            value = padded[index]
            if column_name not in inferred_types:
                inferred_types[column_name] = infer_value_type(value)
            elif inferred_types[column_name] == "string":
                continue
            else:
                current_type = infer_value_type(value)
                if current_type == "string" and inferred_types[column_name] != "string":
                    inferred_types[column_name] = "string"
                elif current_type == "float" and inferred_types[column_name] == "int":
                    inferred_types[column_name] = "float"

    return {
        "relative_path": str(relative_path),
        "filename": path.name,
        "extension": path.suffix.lower(),
        "file_size_bytes": path.stat().st_size,
        "file_size_mb": round(path.stat().st_size / (1024 * 1024), 6),
        "row_count": len(data_rows),
        "column_count": column_count,
        "column_names": column_names,
        "data_types": inferred_types,
        "missing_values": missing_values,
        "duplicate_row_count": duplicate_rows,
        "sheet_names": [],
        "sheet_details": [],
    }


def inventory_excel_workbook(path: Path) -> dict[str, Any]:
    """Inventory an Excel workbook without modifying the file."""
    if load_workbook is None:
        raise RuntimeError(
            "Missing dependency: openpyxl is required to inspect .xlsx files. "
            "Install openpyxl only after explicit approval."
        )

    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet_details = []
    all_sheet_names = list(workbook.sheetnames)

    for sheet_name in all_sheet_names:
        sheet = workbook[sheet_name]
        rows = list(sheet.iter_rows(values_only=True))
        non_empty_rows = [
            row
            for row in rows
            if any(value is not None and str(value).strip() != "" for value in row)
        ]

        if not non_empty_rows:
            row_count = 0
            column_count = 0
            columns = []
            data_types = {}
            missing_values = {}
            duplicate_row_count = 0
            contains_data = False
        else:
            header = list(non_empty_rows[0])
            clean_header = [
                str(value) if value is not None else "Column_{}".format(index + 1)
                for index, value in enumerate(header)
            ]
            column_count = len(clean_header)
            columns = clean_header
            data_rows = non_empty_rows[1:]
            data_types = {name: "string" for name in clean_header}
            missing_values = {name: 0 for name in clean_header}
            seen_rows: set[tuple[Any, ...]] = set()
            duplicate_row_count = 0

            for row in data_rows:
                normalized = list(row[:column_count]) + [None] * max(
                    0, column_count - len(row)
                )
                seen_key = tuple(normalized)
                if seen_key in seen_rows:
                    duplicate_row_count += 1
                else:
                    seen_rows.add(seen_key)

                for index, value in enumerate(normalized):
                    column_name = clean_header[index]
                    if normalize_missing(value):
                        missing_values[column_name] += 1
                    if column_name in data_types:
                        current_type = infer_value_type(value)
                        if current_type == "string":
                            data_types[column_name] = "string"
                        elif data_types[column_name] == "string":
                            pass
                        elif (
                            data_types[column_name] == "int" and current_type == "float"
                        ):
                            data_types[column_name] = "float"
                        elif (
                            data_types[column_name] in {"float", "int"}
                            and current_type == "bool"
                        ):
                            data_types[column_name] = "string"

            contains_data = True
            row_count = len(data_rows)

        sheet_details.append(
            {
                "sheet_name": sheet_name,
                "row_count": row_count,
                "column_count": column_count,
                "column_names": columns,
                "data_types": data_types,
                "missing_values": missing_values,
                "duplicate_row_count": duplicate_row_count,
                "contains_data": contains_data,
            }
        )

    workbook.close()

    return {
        "relative_path": safe_relative_path(path),
        "filename": path.name,
        "extension": path.suffix.lower(),
        "file_size_bytes": path.stat().st_size,
        "file_size_mb": round(path.stat().st_size / (1024 * 1024), 6),
        "row_count": max((detail["row_count"] for detail in sheet_details), default=0),
        "column_count": max(
            (detail["column_count"] for detail in sheet_details), default=0
        ),
        "column_names": [
            name for detail in sheet_details for name in detail["column_names"]
        ],
        "data_types": {
            key: value
            for detail in sheet_details
            for key, value in detail["data_types"].items()
        },
        "missing_values": {
            key: value
            for detail in sheet_details
            for key, value in detail["missing_values"].items()
        },
        "duplicate_row_count": sum(
            detail["duplicate_row_count"] for detail in sheet_details
        ),
        "sheet_names": all_sheet_names,
        "sheet_details": sheet_details,
    }


def inventory_xls_file(path: Path) -> dict[str, Any]:
    """Inventory an XLS file without modifying the file."""
    if xlrd is None:
        raise RuntimeError(
            "Missing dependency: xlrd is required to inspect .xls files. "
            "Install xlrd only after explicit approval."
        )

    workbook = xlrd.open_workbook(path)
    sheet_details = []
    for sheet_name in workbook.sheet_names():
        sheet = workbook.sheet_by_name(sheet_name)
        rows = [sheet.row_values(row_index) for row_index in range(sheet.nrows)]
        non_empty_rows = [
            row for row in rows if any(str(value).strip() != "" for value in row)
        ]
        if not non_empty_rows:
            row_count = 0
            column_count = 0
            columns = []
            data_types = {}
            missing_values = {}
            duplicate_row_count = 0
            contains_data = False
        else:
            header = [
                str(value) if value is not None else f"Column_{idx + 1}"
                for idx, value in enumerate(non_empty_rows[0])
            ]
            column_count = len(header)
            columns = header
            data_rows = non_empty_rows[1:]
            data_types = {name: "string" for name in header}
            missing_values = {name: 0 for name in header}
            seen_rows: set[tuple[Any, ...]] = set()
            duplicate_row_count = 0

            for row in data_rows:
                normalized = list(row[:column_count]) + [None] * max(
                    0, column_count - len(row)
                )
                seen_key = tuple(normalized)
                if seen_key in seen_rows:
                    duplicate_row_count += 1
                else:
                    seen_rows.add(seen_key)
                for index, value in enumerate(normalized):
                    column_name = header[index]
                    if normalize_missing(value):
                        missing_values[column_name] += 1
                    current_type = infer_value_type(value)
                    if current_type == "string":
                        data_types[column_name] = "string"
                    elif data_types[column_name] == "string":
                        continue
                    elif data_types[column_name] == "int" and current_type == "float":
                        data_types[column_name] = "float"
                    elif current_type == "float" and data_types[column_name] == "int":
                        data_types[column_name] = "float"

            row_count = len(data_rows)
            contains_data = True

        sheet_details.append(
            {
                "sheet_name": sheet_name,
                "row_count": row_count,
                "column_count": column_count,
                "column_names": columns,
                "data_types": data_types,
                "missing_values": missing_values,
                "duplicate_row_count": duplicate_row_count,
                "contains_data": contains_data,
            }
        )

    return {
        "relative_path": safe_relative_path(path),
        "filename": path.name,
        "extension": path.suffix.lower(),
        "file_size_bytes": path.stat().st_size,
        "file_size_mb": round(path.stat().st_size / (1024 * 1024), 6),
        "row_count": max((detail["row_count"] for detail in sheet_details), default=0),
        "column_count": max(
            (detail["column_count"] for detail in sheet_details), default=0
        ),
        "column_names": [
            name for detail in sheet_details for name in detail["column_names"]
        ],
        "data_types": {
            key: value
            for detail in sheet_details
            for key, value in detail["data_types"].items()
        },
        "missing_values": {
            key: value
            for detail in sheet_details
            for key, value in detail["missing_values"].items()
        },
        "duplicate_row_count": sum(
            detail["duplicate_row_count"] for detail in sheet_details
        ),
        "sheet_names": workbook.sheet_names(),
        "sheet_details": sheet_details,
    }


def inventory_dataset_file(path: Path) -> dict[str, Any]:
    """Inventory a supported dataset file by extension."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return inventory_csv_file(path)
    if suffix == ".xlsx":
        return inventory_excel_workbook(path)
    if suffix == ".xls":
        return inventory_xls_file(path)
    raise ValueError(f"Unsupported file type for inventory: {path}")


def build_inventory(root: Path) -> dict[str, Any]:
    """Build a dataset inventory document for the raw-data directory."""
    files = discover_dataset_files(root)
    unsupported = find_unsupported_files(root)
    if unsupported:
        names = ", ".join(safe_relative_path(path) for path in unsupported)
        raise ValueError(f"Unsupported file types found under data/raw: {names}")

    dataset_entries = [inventory_dataset_file(path) for path in files]

    quality_summary = {
        "total_file_count": len(dataset_entries),
        "total_row_count": sum(item["row_count"] for item in dataset_entries),
        "total_column_count": sum(item["column_count"] for item in dataset_entries),
        "files_missing_rows": sum(
            1 for item in dataset_entries if item["row_count"] == 0
        ),
        "files_with_duplicate_rows": sum(
            1 for item in dataset_entries if item["duplicate_row_count"] > 0
        ),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inventory_schema_version": "1.0",
        "datasets": dataset_entries,
        "file_metadata": dataset_entries,
        "schema_metadata": {
            "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
            "raw_data_root": "data/raw",
        },
        "quality_summary": quality_summary,
    }


def write_inventory_json(payload: dict[str, Any], output_path: Path) -> None:
    """Persist the inventory payload as JSON in the metadata folder."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_inventory_markdown(payload: dict[str, Any], output_path: Path) -> None:
    """Persist a human-readable markdown summary in the metadata folder."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Dataset Inventory Report",
        "",
        f"Generated at: {payload['generated_at']}",
        "",
        "## Summary",
        f"- Total files: {payload['quality_summary']['total_file_count']}",
        f"- Total rows: {payload['quality_summary']['total_row_count']}",
        f"- Total columns: {payload['quality_summary']['total_column_count']}",
        f"- Files with duplicate rows: {payload['quality_summary']['files_with_duplicate_rows']}",
        "",
    ]

    for item in payload["datasets"]:
        lines.append(f"## {item['filename']}")
        lines.append(f"- Relative path: {item['relative_path']}")
        lines.append(f"- File type: {item['extension']}")
        lines.append(
            f"- File size: {item['file_size_bytes']} bytes ({item['file_size_mb']} MB)"
        )
        lines.append(f"- Row count: {item['row_count']}")
        lines.append(f"- Column count: {item['column_count']}")
        lines.append(
            f"- Columns: {', '.join(item['column_names']) if item['column_names'] else 'Not available'}"
        )
        lines.append(f"- Data types: {json.dumps(item['data_types'], sort_keys=True)}")
        lines.append(
            f"- Missing values: {json.dumps(item['missing_values'], sort_keys=True)}"
        )
        lines.append(f"- Duplicate rows: {item['duplicate_row_count']}")
        if item.get("sheet_names"):
            lines.append(f"- Sheet names: {', '.join(item['sheet_names'])}")
        lines.append("")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """Run the dataset inventory tool."""
    try:
        inventory = build_inventory(RAW_DATA_DIR)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Missing dependency: {exc}", file=sys.stderr)
        return 1

    write_inventory_json(inventory, METADATA_DIR / "dataset_inventory.json")
    write_inventory_markdown(inventory, METADATA_DIR / "dataset_inventory.md")
    print(f"Inventory generated for {len(inventory['datasets'])} dataset file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
