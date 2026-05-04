import os
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DOCS_DIR = PROJECT_ROOT / "docs"

OUTPUT_PATH = DOCS_DIR / "data_inventory.md"


def inspect_csv_file(file_path: Path) -> dict:
    df = pd.read_csv(file_path)

    total_rows = len(df)
    total_columns = len(df.columns)

    null_counts = df.isna().sum()
    duplicate_rows = df.duplicated().sum()

    columns_info = []

    for column in df.columns:
        columns_info.append(
            {
                "column": column,
                "dtype": str(df[column].dtype),
                "null_count": int(null_counts[column]),
                "null_percentage": round(
                    (null_counts[column] / total_rows) * 100, 2
                )
                if total_rows > 0
                else 0,
                "unique_values": int(df[column].nunique(dropna=True)),
            }
        )

    return {
        "file_name": file_path.name,
        "total_rows": total_rows,
        "total_columns": total_columns,
        "duplicate_rows": int(duplicate_rows),
        "columns_info": columns_info,
    }


def write_inventory_report(results: list[dict]) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("# Raw Data Inventory — Olist Dataset\n\n")

        file.write("## Purpose\n\n")
        file.write(
            "This document summarizes the structure and quality profile "
            "of the raw Olist CSV files before loading them into staging tables.\n\n"
        )

        file.write("## Source Files Summary\n\n")
        file.write("| File | Rows | Columns | Duplicate Rows |\n")
        file.write("|---|---:|---:|---:|\n")

        for result in results:
            file.write(
                f"| {result['file_name']} "
                f"| {result['total_rows']} "
                f"| {result['total_columns']} "
                f"| {result['duplicate_rows']} |\n"
            )

        file.write("\n---\n\n")

        for result in results:
            file.write(f"## {result['file_name']}\n\n")
            file.write(f"- Rows: `{result['total_rows']}`\n")
            file.write(f"- Columns: `{result['total_columns']}`\n")
            file.write(f"- Duplicate rows: `{result['duplicate_rows']}`\n\n")

            file.write("| Column | Type | Null Count | Null % | Unique Values |\n")
            file.write("|---|---|---:|---:|---:|\n")

            for column_info in result["columns_info"]:
                file.write(
                    f"| {column_info['column']} "
                    f"| {column_info['dtype']} "
                    f"| {column_info['null_count']} "
                    f"| {column_info['null_percentage']} "
                    f"| {column_info['unique_values']} |\n"
                )

            file.write("\n---\n\n")


def main() -> None:
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Raw data directory not found: {RAW_DATA_DIR}")

    csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {RAW_DATA_DIR}")

    results = []

    print("========== RAW DATA INVENTORY ==========")

    for file_path in csv_files:
        print(f"Inspecting: {file_path.name}")
        result = inspect_csv_file(file_path)
        results.append(result)

    write_inventory_report(results)

    print("========== INVENTORY COMPLETE ==========")
    print(f"Report generated at: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()