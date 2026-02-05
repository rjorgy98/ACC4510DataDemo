# ACC4510DataDemoLRJ

This repository provides a simple workflow for analyzing the `je_samples.xlsx` journal entry export and producing basic summary statistics in a reusable format.

## What the analysis produces
Running the analysis script generates an `outputs/` folder with:
- `summary.json`: structured metrics for automation or downstream reporting.
- `summary.md`: a human-readable summary.
- `column_summary.csv`: per-column completeness and unique counts.
- `date_summary.csv`: detected date ranges (if any).
- `numeric_stats.csv`: descriptive statistics for numeric columns (if any).

Running the visual report workflow generates a `report_outputs/` folder with:
- `report.md`: a markdown report with embedded visuals.
- `missing_values.png`: bar chart of missing values by column.
- `numeric_distribution.png`: histogram of the main numeric field.
- `benford_analysis.png`: Benford's Law comparison chart.

## Running locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/analyze_je_samples.py --input je_samples.xlsx --output outputs
```

To build the visual report with Benford's Law analysis (using the Amount column in Excel column O):
```bash
python scripts/build_je_report.py --input je_samples.xlsx --output report_outputs --column-name Amount --column-letter O
```

## GitHub Actions
A workflow runs the same analysis on each push or manual trigger and uploads the `outputs/` folder as a downloadable artifact.

A second workflow generates the visual report with Benford's Law analysis and uploads the `report_outputs/` folder.
