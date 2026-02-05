# ACC4510DataDemoLRJ

This repository provides a simple workflow for analyzing the `je_samples.xlsx` journal entry export and producing basic summary statistics in a reusable format.

## What the analysis produces
Running the analysis script generates an `outputs/` folder with:
- `summary.json`: structured metrics for automation or downstream reporting.
- `summary.md`: a human-readable summary.
- `column_summary.csv`: per-column completeness and unique counts.
- `date_summary.csv`: detected date ranges (if any).
- `numeric_stats.csv`: descriptive statistics for numeric columns (if any).

## Running locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/analyze_je_samples.py --input je_samples.xlsx --output outputs
```

## GitHub Actions
A workflow runs the same analysis on each push or manual trigger and uploads the `outputs/` folder as a downloadable artifact.
