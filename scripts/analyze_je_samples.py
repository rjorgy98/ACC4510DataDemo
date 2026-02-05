#!/usr/bin/env python3
"""Basic analysis for journal entry samples."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd


DATE_PARSE_THRESHOLD = 0.1


def detect_date_columns(df: pd.DataFrame) -> dict[str, pd.Series]:
    date_columns: dict[str, pd.Series] = {}
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_datetime64_any_dtype(series):
            date_columns[column] = series
            continue
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            parsed = pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
            if parsed.notna().mean() >= DATE_PARSE_THRESHOLD:
                date_columns[column] = parsed
    return date_columns


def build_summary(df: pd.DataFrame) -> dict:
    overall = {
        "row_count": int(len(df)),
        "column_count": int(df.shape[1]),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_values_total": int(df.isna().sum().sum()),
    }

    column_summary = []
    for column in df.columns:
        series = df[column]
        column_summary.append(
            {
                "column": column,
                "dtype": str(series.dtype),
                "non_null_count": int(series.notna().sum()),
                "null_count": int(series.isna().sum()),
                "unique_count": int(series.nunique(dropna=True)),
            }
        )

    date_columns = detect_date_columns(df)
    date_summary = []
    for column, series in date_columns.items():
        non_null_series = series.dropna()
        date_summary.append(
            {
                "column": column,
                "non_null_count": int(non_null_series.shape[0]),
                "min_date": non_null_series.min().isoformat() if not non_null_series.empty else None,
                "max_date": non_null_series.max().isoformat() if not non_null_series.empty else None,
            }
        )

    numeric_columns = df.select_dtypes(include="number")
    numeric_stats = {}
    if not numeric_columns.empty:
        for column in numeric_columns.columns:
            series = numeric_columns[column]
            numeric_stats[column] = {
                "count": float(series.count()),
                "mean": float(series.mean()) if series.count() else None,
                "std": float(series.std()) if series.count() else None,
                "min": float(series.min()) if series.count() else None,
                "25%": float(series.quantile(0.25)) if series.count() else None,
                "50%": float(series.median()) if series.count() else None,
                "75%": float(series.quantile(0.75)) if series.count() else None,
                "max": float(series.max()) if series.count() else None,
                "sum": float(series.sum()) if series.count() else None,
            }

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "overall": overall,
        "column_summary": column_summary,
        "date_summary": date_summary,
        "numeric_stats": numeric_stats,
    }


def write_outputs(summary: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "summary.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    column_summary_df = pd.DataFrame(summary["column_summary"])
    column_summary_df.to_csv(output_dir / "column_summary.csv", index=False)

    date_summary_df = pd.DataFrame(summary["date_summary"])
    if not date_summary_df.empty:
        date_summary_df.to_csv(output_dir / "date_summary.csv", index=False)

    numeric_stats_df = pd.DataFrame.from_dict(summary["numeric_stats"], orient="index")
    if not numeric_stats_df.empty:
        numeric_stats_df.to_csv(output_dir / "numeric_stats.csv", index_label="column")

    md_lines = [
        "# Journal Entry Sample Summary",
        "",
        "## Overall",
        f"- Rows: {summary['overall']['row_count']}",
        f"- Columns: {summary['overall']['column_count']}",
        f"- Duplicate rows: {summary['overall']['duplicate_rows']}",
        f"- Total missing values: {summary['overall']['missing_values_total']}",
        "",
        "## Date Ranges",
    ]
    if summary["date_summary"]:
        for item in summary["date_summary"]:
            md_lines.append(
                f"- {item['column']}: {item['min_date']} to {item['max_date']} ({item['non_null_count']} non-null)"
            )
    else:
        md_lines.append("- No date-like columns detected.")

    md_lines.extend(["", "## Numeric Statistics", ""])
    if summary["numeric_stats"]:
        for column, stats in summary["numeric_stats"].items():
            md_lines.append(f"### {column}")
            md_lines.append("")
            md_lines.append(
                f"- Count: {stats['count']} | Mean: {stats['mean']} | Std: {stats['std']} | Min: {stats['min']} | Max: {stats['max']} | Sum: {stats['sum']}"
            )
            md_lines.append("")
    else:
        md_lines.append("No numeric columns detected.")

    (output_dir / "summary.md").write_text("\n".join(md_lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze JE sample Excel file.")
    parser.add_argument("--input", default="je_samples.xlsx", help="Path to Excel file")
    parser.add_argument("--output", default="outputs", help="Output directory")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    df = pd.read_excel(input_path)
    summary = build_summary(df)
    write_outputs(summary, output_dir)


if __name__ == "__main__":
    main()
