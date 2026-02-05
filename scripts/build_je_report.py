#!/usr/bin/env python3
"""Generate a visual report with Benford's Law analysis."""
from __future__ import annotations

import argparse
import math
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def resolve_amount_column(df: pd.DataFrame, column_name: str | None, column_letter: str | None) -> str:
    if column_name:
        if column_name in df.columns:
            return column_name
        for col in df.columns:
            if str(col).strip().lower() == column_name.strip().lower():
                return col

    if column_letter:
        letter = column_letter.strip().upper()
        if len(letter) == 1 and letter.isalpha():
            index = ord(letter) - ord("A")
            if 0 <= index < len(df.columns):
                return str(df.columns[index])

    raise SystemExit(
        f"Could not find amount column. Column name '{column_name}' or column letter '{column_letter}' not found."
    )


def first_digit(value: float) -> int | None:
    if value == 0 or math.isnan(value):
        return None
    value = abs(value)
    while value >= 10:
        value /= 10
    while value < 1:
        value *= 10
    return int(value)


def compute_benford_distribution(series: pd.Series) -> pd.DataFrame:
    digits = list(range(1, 10))
    expected = [math.log10(1 + 1 / d) for d in digits]
    observed_counts = {digit: 0 for digit in digits}
    for value in series:
        digit = first_digit(float(value))
        if digit in observed_counts:
            observed_counts[digit] += 1
    total = sum(observed_counts.values())
    observed = [observed_counts[d] / total if total else 0 for d in digits]
    return pd.DataFrame(
        {
            "digit": digits,
            "observed": observed,
            "expected": expected,
        }
    )


def plot_missing_values(df: pd.DataFrame, output_path: Path) -> bool:
    missing = df.isna().sum().sort_values(ascending=False)
    missing = missing[missing > 0]
    if missing.empty:
        return False
    plt.figure(figsize=(10, 6))
    missing.head(15).plot(kind="bar")
    plt.title("Top Missing Values by Column")
    plt.ylabel("Missing Count")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    return True


def plot_numeric_distribution(series: pd.Series, column: str, output_path: Path) -> bool:
    if series.empty:
        return False
    plt.figure(figsize=(10, 6))
    plt.hist(series, bins=30, color="#4C78A8", edgecolor="white")
    plt.title(f"Distribution of {column}")
    plt.xlabel(column)
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    return True


def plot_benford(benford_df: pd.DataFrame, output_path: Path, column: str) -> bool:
    if benford_df.empty:
        return False
    plt.figure(figsize=(10, 6))
    plt.bar(benford_df["digit"] - 0.2, benford_df["observed"], width=0.4, label="Observed")
    plt.bar(benford_df["digit"] + 0.2, benford_df["expected"], width=0.4, label="Expected")
    plt.title(f"Benford's Law Comparison for {column}")
    plt.xlabel("Leading Digit")
    plt.ylabel("Proportion")
    plt.xticks(benford_df["digit"])
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    return True


def build_report(df: pd.DataFrame, output_dir: Path, amount_column: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    missing_plot_path = output_dir / "missing_values.png"
    numeric_plot_path = output_dir / "numeric_distribution.png"
    benford_plot_path = output_dir / "benford_analysis.png"

    has_missing_plot = plot_missing_values(df, missing_plot_path)

    column = amount_column
    series = pd.to_numeric(df[column], errors="coerce").dropna().astype(float).abs()
    series = series[series >= 1]
    has_numeric_plot = False
    benford_df = pd.DataFrame()
    has_benford_plot = False
    if not series.empty:
        has_numeric_plot = plot_numeric_distribution(series, column, numeric_plot_path)
        benford_df = compute_benford_distribution(series)
        has_benford_plot = plot_benford(benford_df, benford_plot_path, column)

    overview = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_values": int(df.isna().sum().sum()),
    }

    report_lines = [
        "# Journal Entry Visual Report",
        "",
        f"Generated at: {datetime.utcnow().isoformat()}Z",
        "",
        "## Data Overview",
        f"- Rows: {overview['rows']}",
        f"- Columns: {overview['columns']}",
        f"- Total missing values: {overview['missing_values']}",
        "",
        "## Visuals",
    ]

    if has_missing_plot:
        report_lines.extend(
            ["### Missing Values", "", f"![Missing values plot]({missing_plot_path.name})", ""]
        )
    else:
        report_lines.append("- Missing values plot not generated (no missing values detected).")

    if has_numeric_plot:
        report_lines.extend(
            ["### Numeric Distribution", "", f"![Numeric distribution plot]({numeric_plot_path.name})", ""]
        )
    else:
        report_lines.append("- Numeric distribution plot not generated (no numeric data detected).")

    if has_benford_plot:
        report_lines.extend(
            ["### Benford's Law Analysis", "", f"![Benford analysis plot]({benford_plot_path.name})", ""]
        )
        report_lines.append("| Digit | Observed | Expected |")
        report_lines.append("| --- | --- | --- |")
        for _, row in benford_df.iterrows():
            report_lines.append(f"| {int(row['digit'])} | {row['observed']:.3f} | {row['expected']:.3f} |")
        report_lines.append("")
    else:
        report_lines.append("- Benford analysis not generated (insufficient numeric data).")

    (output_dir / "report.md").write_text("\n".join(report_lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a JE visual report with Benford analysis.")
    parser.add_argument("--input", default="je_samples.xlsx", help="Path to Excel file")
    parser.add_argument("--output", default="report_outputs", help="Output directory")
    parser.add_argument(
        "--column-name",
        default="Amount",
        help="Name of the amount column to analyze (defaults to Amount).",
    )
    parser.add_argument(
        "--column-letter",
        default="O",
        help="Excel column letter for the amount field (defaults to O).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    df = pd.read_excel(input_path)
    amount_column = resolve_amount_column(df, args.column_name, args.column_letter)
    build_report(df, Path(args.output), amount_column)


if __name__ == "__main__":
    main()
