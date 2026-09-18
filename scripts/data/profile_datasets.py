"""Read-only dataset profiling utilities for workbook analysis.

This module profiles supported raw data files and writes summaries to the metadata
folder without modifying source datasets.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

RAW_DATA_DIR = Path("data/raw")
METADATA_DIR = Path("data/metadata")
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover
    load_workbook = None


def discover_dataset_files(root: Path) -> list[Path]:
    """Return dataset files found under the raw-data directory."""
    if not root.exists():
        raise FileNotFoundError(f"Raw data directory does not exist: {root}")

    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == ".gitkeep":
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return files


def safe_relative_path(path: Path) -> str:
    """Return a repo-relative path when possible, else fall back to a stable path."""
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return path.as_posix()


def coerce_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    return value


def normalize_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        text = value.strip()
        return text.lower() in {"", "na", "n/a", "null", "none", "nan"}
    return False


def infer_column_type(values: list[Any]) -> str:
    """Infer a conservative column type: text/numeric/date-like/mixed/empty."""
    non_missing = [v for v in values if not normalize_missing(v)]
    if not non_missing:
        return "empty"

    detected: set[str] = set()
    for value in non_missing:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            detected.add("numeric")
            continue

        text = str(value).strip()
        if text == "":
            continue
        try:
            float(text)
            detected.add("numeric")
            continue
        except ValueError:
            pass

        try:
            from datetime import datetime as dt

            dt.strptime(text, "%Y-%m-%d")
            detected.add("date-like")
            continue
        except ValueError:
            pass

        try:
            from datetime import datetime as dt

            dt.strptime(text, "%d/%m/%Y")
            detected.add("date-like")
            continue
        except ValueError:
            pass

        detected.add("text")

    if not detected:
        return "empty"
    if len(detected) == 1:
        return next(iter(detected))
    if "numeric" in detected and "text" in detected:
        return "mixed"
    if "numeric" in detected and "date-like" in detected:
        return "mixed"
    if "text" in detected and "date-like" in detected:
        return "mixed"
    return "mixed"


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_date_column_name(column_name: str) -> bool:
    """Return True for the invoice-date style columns used in the workbook."""
    normalized = "".join(ch for ch in str(column_name).lower() if ch.isalnum())
    return normalized in {"invoicedate", "date", "orderdate"}


def is_identifier_like(column_name: str) -> bool:
    """Return True for columns that are logically identifiers, not quality warnings."""
    normalized = "".join(ch for ch in str(column_name).lower() if ch.isalnum())
    return (
        normalized
        in {
            "invoice",
            "stockcode",
            "customerid",
            "customer",
            "orderid",
            "id",
        }
        or normalized.startswith("invoice")
        or normalized.startswith("stockcode")
    )


def safe_date(value: Any) -> bool:
    """Return True only when the value is a valid date-like value."""
    if value is None:
        return False
    if isinstance(value, datetime):
        return True
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        return True

    text = str(value).strip()
    if not text:
        return False

    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    ):
        try:
            datetime.strptime(text, fmt)
            return True
        except ValueError:
            continue
    return False


def compute_numeric_summary(values: list[Any]) -> dict[str, Any]:
    numeric = [float(v) for v in values if safe_float(v) is not None]
    if not numeric:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "sum": None,
            "stddev": None,
        }

    numeric_sorted = sorted(numeric)
    count = len(numeric)
    total = sum(numeric)
    mean = total / count
    mid = count // 2
    if count % 2 == 0:
        median = (numeric_sorted[mid - 1] + numeric_sorted[mid]) / 2
    else:
        median = numeric_sorted[mid]
    variance = sum((v - mean) ** 2 for v in numeric) / count
    stddev = math.sqrt(variance)

    return {
        "count": count,
        "min": numeric_sorted[0],
        "max": numeric_sorted[-1],
        "mean": mean,
        "median": median,
        "sum": total,
        "stddev": stddev,
    }


def compute_common_values(values: list[Any], limit: int = 5) -> list[dict[str, Any]]:
    counts = Counter(str(v).strip() for v in values if not normalize_missing(v))
    return [
        {"value": value, "count": count} for value, count in counts.most_common(limit)
    ]


def compute_invoice_date_metrics(
    rows: list[dict[str, Any]], column_names: list[str]
) -> dict[str, Any]:
    """Compute InvoiceDate metrics directly from worksheet rows without persisting raw rows."""
    invoice_column = None
    for idx, name in enumerate(column_names):
        if is_date_column_name(name):
            invoice_column = idx
            break

    metrics = {
        "non_empty_count": 0,
        "valid_date_count": 0,
        "invalid_date_count": 0,
        "date_parsing_issues": [],
    }

    if invoice_column is None:
        return metrics

    for row in rows:
        value = row.get(column_names[invoice_column])
        if normalize_missing(value):
            continue
        metrics["non_empty_count"] += 1
        if safe_date(value):
            metrics["valid_date_count"] += 1
            continue
        metrics["invalid_date_count"] += 1
        metrics["date_parsing_issues"].append(
            {"column": column_names[invoice_column], "value": value}
        )

    return metrics


def compute_quality_checks_for_sheet(
    sheet: dict[str, Any], row_records: list[dict[str, Any]]
) -> dict[str, Any]:
    """Compute targeted quality checks for a profiled sheet without persisting raw rows."""
    checks: dict[str, Any] = {
        "empty_columns": [],
        "mixed_type_columns": [],
        "date_parsing_issues": [],
        "negative_quantities": [],
        "zero_quantities": [],
        "negative_prices": [],
        "zero_prices": [],
        "unusually_large_quantities": [],
        "unusually_large_prices": [],
        "duplicate_rows": 0,
    }

    seen: set[tuple[Any, ...]] = set()
    for row in row_records:
        key = tuple(row.get(col["name"], None) for col in sheet["columns"])
        if key in seen:
            checks["duplicate_rows"] += 1
        else:
            seen.add(key)

    for column in sheet["columns"]:
        if column["inferred_type"] == "empty":
            checks["empty_columns"].append({"column": column["name"]})
        if column["inferred_type"] == "mixed" and not is_identifier_like(
            column["name"]
        ):
            checks["mixed_type_columns"].append({"column": column["name"]})

        values = [row.get(column["name"]) for row in row_records]
        lower_name = column["name"].lower()
        for value in values:
            if lower_name in {"quantity", "qty"}:
                number = safe_float(value)
                if number is not None and number < 0:
                    checks["negative_quantities"].append(
                        {"column": column["name"], "value": value}
                    )
                if number == 0:
                    checks["zero_quantities"].append(
                        {"column": column["name"], "value": value}
                    )
                if number is not None and abs(number) > 100000:
                    checks["unusually_large_quantities"].append(
                        {"column": column["name"], "value": value}
                    )
            if lower_name in {"price", "unit_price"}:
                number = safe_float(value)
                if number is not None and number < 0:
                    checks["negative_prices"].append(
                        {"column": column["name"], "value": value}
                    )
                if number == 0:
                    checks["zero_prices"].append(
                        {"column": column["name"], "value": value}
                    )
                if number is not None and abs(number) > 10000:
                    checks["unusually_large_prices"].append(
                        {"column": column["name"], "value": value}
                    )

        if is_date_column_name(column["name"]):
            for row in row_records:
                value = row.get(column["name"])
                if normalize_missing(value):
                    continue
                if not safe_date(value):
                    checks["date_parsing_issues"].append(
                        {"column": column["name"], "value": value}
                    )

    return checks


def profile_excel_sheet(sheet) -> dict[str, Any]:
    rows = list(sheet.iter_rows(values_only=True))
    non_empty_rows = [
        row
        for row in rows
        if any(value is not None and str(value).strip() != "" for value in row)
    ]
    if not non_empty_rows:
        return {
            "sheet_name": sheet.title,
            "row_count": 0,
            "column_count": 0,
            "column_names": [],
            "columns": [],
            "invoice_date_metrics": {
                "non_empty_count": 0,
                "valid_date_count": 0,
                "invalid_date_count": 0,
                "date_parsing_issues": [],
            },
            "quality_checks": {
                "empty_columns": [],
                "mixed_type_columns": [],
                "date_parsing_issues": [],
                "negative_quantities": [],
                "zero_quantities": [],
                "negative_prices": [],
                "zero_prices": [],
                "unusually_large_quantities": [],
                "unusually_large_prices": [],
                "duplicate_rows": 0,
            },
        }

    header = list(non_empty_rows[0])
    column_names = [
        str(value) if value is not None else f"Column_{idx + 1}"
        for idx, value in enumerate(header)
    ]
    data_rows = non_empty_rows[1:]
    row_records = [
        {
            column_names[index]: row[index] if index < len(row) else None
            for index in range(len(column_names))
        }
        for row in data_rows
    ]

    column_entries = []
    for idx, column_name in enumerate(column_names):
        values = [row[idx] if idx < len(row) else None for row in data_rows]
        non_missing_values = [v for v in values if not normalize_missing(v)]
        missing_count = sum(1 for v in values if normalize_missing(v))
        missing_percentage = (missing_count / len(values)) * 100 if values else 0.0
        unique_count = len(set(str(v).strip() for v in non_missing_values))
        inferred_type = infer_column_type(values)

        stats: dict[str, Any] = {
            "inferred_type": inferred_type,
            "missing_count": missing_count,
            "missing_percentage": round(missing_percentage, 4),
            "unique_count": unique_count,
            "values": [],
        }

        if inferred_type in {"numeric", "mixed"}:
            numeric_values = [
                safe_float(v) for v in values if safe_float(v) is not None
            ]
            if numeric_values:
                stats["numeric_summary"] = compute_numeric_summary(values)
        if inferred_type in {"date-like", "mixed"}:
            date_values = [
                str(v).strip()
                for v in values
                if not normalize_missing(v) and safe_date(v)
            ]
            stats["date_valid_count"] = len(date_values)
        if inferred_type in {"text", "mixed"}:
            stats["common_values"] = compute_common_values(values)

        stats["empty_column"] = inferred_type == "empty"
        stats["min"] = None
        stats["max"] = None
        numeric_values = [safe_float(v) for v in values if safe_float(v) is not None]
        if numeric_values:
            stats["min"] = min(numeric_values)
            stats["max"] = max(numeric_values)

        column_entries.append({"name": column_name, **stats})

    invoice_date_metrics = compute_invoice_date_metrics(row_records, column_names)
    sheet_profile = {
        "sheet_name": sheet.title,
        "row_count": len(data_rows),
        "column_count": len(column_names),
        "column_names": column_names,
        "columns": column_entries,
        "invoice_date_metrics": invoice_date_metrics,
        "mixed_type_columns": [
            {"column": column["name"]}
            for column in column_entries
            if column["inferred_type"] == "mixed"
        ],
    }
    sheet_profile["quality_checks"] = compute_quality_checks_for_sheet(
        sheet_profile, row_records
    )
    sheet_profile["quality_checks"]["date_parsing_issues"] = invoice_date_metrics[
        "date_parsing_issues"
    ]
    return sheet_profile


def profile_excel_workbook(path: Path) -> dict[str, Any]:
    """Profile an Excel workbook without modifying the file."""
    if load_workbook is None:
        raise RuntimeError(
            "Missing dependency: openpyxl is required to inspect .xlsx files. "
            "Install openpyxl only after explicit approval."
        )

    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet_profiles = [
        profile_excel_sheet(workbook[sheet_name]) for sheet_name in workbook.sheetnames
    ]
    workbook.close()

    aggregate = {
        "empty_columns": [],
        "mixed_type_columns": [],
        "date_parsing_issues": [],
        "negative_quantities": [],
        "zero_quantities": [],
        "negative_prices": [],
        "zero_prices": [],
        "unusually_large_quantities": [],
        "unusually_large_prices": [],
        "duplicate_rows": sum(
            sheet["quality_checks"]["duplicate_rows"] for sheet in sheet_profiles
        ),
    }
    total_invoice_date_metrics = {
        "non_empty_count": sum(
            sheet["invoice_date_metrics"]["non_empty_count"] for sheet in sheet_profiles
        ),
        "valid_date_count": sum(
            sheet["invoice_date_metrics"]["valid_date_count"]
            for sheet in sheet_profiles
        ),
        "invalid_date_count": sum(
            sheet["invoice_date_metrics"]["invalid_date_count"]
            for sheet in sheet_profiles
        ),
        "date_parsing_issues": [
            issue
            for sheet in sheet_profiles
            for issue in sheet["invoice_date_metrics"]["date_parsing_issues"]
        ],
    }
    for sheet in sheet_profiles:
        for key in [
            "empty_columns",
            "mixed_type_columns",
            "date_parsing_issues",
            "negative_quantities",
            "zero_quantities",
            "negative_prices",
            "zero_prices",
            "unusually_large_quantities",
            "unusually_large_prices",
        ]:
            aggregate[key].extend(sheet["quality_checks"].get(key, []))

    result = {
        "relative_path": safe_relative_path(path),
        "filename": path.name,
        "extension": path.suffix.lower(),
        "file_size_bytes": path.stat().st_size,
        "file_size_mb": round(path.stat().st_size / (1024 * 1024), 6),
        "sheet_count": len(sheet_profiles),
        "sheet_names": [sheet["sheet_name"] for sheet in sheet_profiles],
        "sheets": sheet_profiles,
        "invoice_date_metrics": total_invoice_date_metrics,
        "mixed_type_columns": [
            {"sheet": sheet["sheet_name"], "column": column["name"]}
            for sheet in sheet_profiles
            for column in sheet["columns"]
            if column["inferred_type"] == "mixed"
        ],
        "quality_checks": aggregate,
    }
    return result


def profile_csv_file(path: Path) -> dict[str, Any]:
    """Profile a CSV file without modifying the source dataset."""
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            rows.append(line.rstrip("\r\n").split(","))

    if not rows:
        return {
            "relative_path": safe_relative_path(path),
            "filename": path.name,
            "extension": path.suffix.lower(),
            "file_size_bytes": path.stat().st_size,
            "file_size_mb": round(path.stat().st_size / (1024 * 1024), 6),
            "sheet_count": 1,
            "sheet_names": [path.stem],
            "sheets": [],
        }

    header = rows[0]
    data_rows = rows[1:]
    row_records = [
        {
            header[index]: row[index] if index < len(row) else None
            for index in range(len(header))
        }
        for row in data_rows
    ]
    sheet_profile = {
        "sheet_name": path.stem,
        "row_count": len(data_rows),
        "column_count": len(header),
        "column_names": header,
        "columns": [],
        "invoice_date_metrics": {
            "non_empty_count": 0,
            "valid_date_count": 0,
            "invalid_date_count": 0,
            "date_parsing_issues": [],
        },
    }

    for idx, column_name in enumerate(header):
        values = [row[idx] if idx < len(row) else None for row in data_rows]
        missing_count = sum(1 for v in values if normalize_missing(v))
        missing_percentage = (missing_count / len(values)) * 100 if values else 0.0
        inferred_type = infer_column_type(values)
        numeric_summary = (
            compute_numeric_summary(values)
            if inferred_type in {"numeric", "mixed"}
            else None
        )
        sheet_profile["columns"].append(
            {
                "name": column_name,
                "inferred_type": inferred_type,
                "missing_count": missing_count,
                "missing_percentage": round(missing_percentage, 4),
                "unique_count": len(
                    {str(v).strip() for v in values if not normalize_missing(v)}
                ),
                "common_values": compute_common_values(values),
                "numeric_summary": numeric_summary,
                "empty_column": inferred_type == "empty",
            }
        )
    sheet_profile["invoice_date_metrics"] = compute_invoice_date_metrics(
        row_records, header
    )
    sheet_profile["quality_checks"] = compute_quality_checks_for_sheet(
        sheet_profile, row_records
    )
    sheet_profile["quality_checks"]["date_parsing_issues"] = sheet_profile[
        "invoice_date_metrics"
    ]["date_parsing_issues"]
    return {
        "relative_path": safe_relative_path(path),
        "filename": path.name,
        "extension": path.suffix.lower(),
        "file_size_bytes": path.stat().st_size,
        "file_size_mb": round(path.stat().st_size / (1024 * 1024), 6),
        "sheet_count": 1,
        "sheet_names": [path.stem],
        "sheets": [sheet_profile],
        "invoice_date_metrics": sheet_profile["invoice_date_metrics"],
        "quality_checks": sheet_profile["quality_checks"],
    }


def profile_dataset_file(path: Path) -> dict[str, Any]:
    """Profile a supported dataset file by extension."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return profile_csv_file(path)
    if suffix in {".xlsx", ".xls"}:
        return profile_excel_workbook(path)
    raise ValueError(f"Unsupported file type for profiling: {path}")


def get_quality_checks(profile: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, Any] = {
        "empty_columns": [],
        "mixed_type_columns": [],
        "date_parsing_issues": [],
        "negative_quantities": [],
        "zero_quantities": [],
        "negative_prices": [],
        "zero_prices": [],
        "unusually_large_quantities": [],
        "unusually_large_prices": [],
        "duplicate_rows": 0,
    }

    for sheet in profile["sheets"]:
        for column in sheet["columns"]:
            if column["inferred_type"] == "empty":
                checks["empty_columns"].append(
                    {"sheet": sheet["sheet_name"], "column": column["name"]}
                )
            if column["inferred_type"] == "mixed":
                checks["mixed_type_columns"].append(
                    {"sheet": sheet["sheet_name"], "column": column["name"]}
                )

        rows = []
        for sheet_name in [sheet["sheet_name"] for sheet in profile["sheets"]]:
            pass

        if not sheet["columns"]:
            continue

        column_names = sheet["column_names"]
        row_values = []
        for row_index in range(sheet["row_count"]):
            row_values.append([])
        # Use cell data from the source workbook is not available here; checks remain best-effort.

    return checks


def generate_profile_payload(profile: dict[str, Any]) -> dict[str, Any]:
    """Wrap a profile result in the standard metadata payload."""
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile_schema_version": "1.0",
        "datasets": [profile],
        "file_metadata": [profile],
        "quality_summary": {
            "total_file_count": 1,
            "total_sheet_count": profile["sheet_count"],
            "total_row_count": sum(sheet["row_count"] for sheet in profile["sheets"]),
            "total_column_count": sum(
                sheet["column_count"] for sheet in profile["sheets"]
            ),
            "files_with_empty_columns": 0,
            "files_with_duplicate_rows": 0,
        },
        "schema_metadata": {
            "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
            "raw_data_root": "data/raw",
        },
    }
    payload["quality_summary"]["files_with_empty_columns"] = sum(
        1
        for sheet in profile["sheets"]
        for col in sheet["columns"]
        if col.get("empty_column")
    )
    payload["quality_summary"]["files_with_duplicate_rows"] = profile.get(
        "quality_checks", {}
    ).get("duplicate_rows", 0)
    return payload


def json_safe(value: Any) -> Any:
    """Convert profiler data into JSON-serializable structures."""
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if key.startswith("_"):
                continue
            cleaned[key] = json_safe(item)
        return cleaned
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if hasattr(value, "isoformat") and callable(value.isoformat):
        try:
            return value.isoformat()
        except TypeError:
            return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def write_profile_json(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(json_safe(payload), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_profile_markdown(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    profile = payload["datasets"][0]
    lines = [
        "# Dataset Profile Report",
        "",
        f"Generated at: {payload['generated_at']}",
        "",
        "## File Summary",
        f"- Relative path: {profile['relative_path']}",
        f"- Filename: {profile['filename']}",
        f"- Extension: {profile['extension']}",
        f"- File size: {profile['file_size_bytes']} bytes ({profile['file_size_mb']} MB)",
        f"- Sheet names: {', '.join(profile['sheet_names'])}",
        "",
        "## Sheet Details",
    ]

    for sheet in profile["sheets"]:
        lines.append(f"### {sheet['sheet_name']}")
        lines.append(f"- Row count: {sheet['row_count']}")
        lines.append(f"- Column count: {sheet['column_count']}")
        lines.append(f"- Columns: {', '.join(sheet['column_names'])}")
        lines.append("")
        lines.append(
            "| Column | Type | Missing count | Missing % | Unique count | Min | Max |"
        )
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for col in sheet["columns"]:
            min_value = (
                col.get("numeric_summary", {}).get("min")
                if col.get("numeric_summary")
                else "-"
            )
            max_value = (
                col.get("numeric_summary", {}).get("max")
                if col.get("numeric_summary")
                else "-"
            )
            lines.append(
                f"| {col['name']} | {col['inferred_type']} | {col['missing_count']} | {col['missing_percentage']} | {col['unique_count']} | {min_value} | {max_value} |"
            )
        lines.append("")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """Run the profiling utility."""
    try:
        files = discover_dataset_files(RAW_DATA_DIR)
        if not files:
            print("ERROR: No dataset files found under data/raw", file=sys.stderr)
            return 1
        ordered = sorted(files, key=lambda p: str(p))
        profiles = [profile_dataset_file(path) for path in ordered]
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "profile_schema_version": "1.0",
            "datasets": profiles,
            "file_metadata": profiles,
            "quality_summary": {
                "total_file_count": len(profiles),
                "total_sheet_count": sum(p["sheet_count"] for p in profiles),
                "total_row_count": sum(
                    sum(sheet["row_count"] for sheet in p["sheets"]) for p in profiles
                ),
                "total_column_count": sum(
                    sum(sheet["column_count"] for sheet in p["sheets"])
                    for p in profiles
                ),
                "files_with_empty_columns": sum(
                    1
                    for p in profiles
                    for s in p["sheets"]
                    for c in s["columns"]
                    if c.get("empty_column")
                ),
                "files_with_duplicate_rows": sum(
                    1
                    for p in profiles
                    if p.get("quality_checks", {}).get("duplicate_rows", 0) > 0
                ),
            },
            "schema_metadata": {
                "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
                "raw_data_root": "data/raw",
            },
        }
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Missing dependency: {exc}", file=sys.stderr)
        return 1

    write_profile_json(payload, METADATA_DIR / "dataset_profile.json")
    write_profile_markdown(payload, METADATA_DIR / "dataset_profile.md")
    print(f"Profiling generated for {len(payload['datasets'])} dataset file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
