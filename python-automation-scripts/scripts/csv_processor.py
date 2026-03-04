"""
csv_processor.py
----------------
Load a CSV file, validate its structure, compute summary statistics,
and export a clean Markdown or JSON report.

Usage:
    python csv_processor.py data.csv --format markdown
    python csv_processor.py data.csv --format json --output report.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def load_csv(path: str) -> list[dict[str, str]]:
    """Read a CSV file and return a list of row dicts."""
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    if file.stat().st_size == 0:
        raise ValueError(f"CSV file is empty: {path}")
    with open(file, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    if not rows:
        raise ValueError("CSV has headers but no data rows.")
    return rows


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    """Compute per-column statistics for a list of CSV row dicts."""
    if not rows:
        return {}

    columns = list(rows[0].keys())
    summary: dict[str, Any] = {
        "total_rows": len(rows),
        "columns": columns,
        "column_stats": {},
    }

    for col in columns:
        values = [row[col] for row in rows if row[col].strip()]
        numeric = []
        for v in values:
            try:
                numeric.append(float(v))
            except ValueError:
                pass

        stats: dict[str, Any] = {
            "non_empty": len(values),
            "empty": len(rows) - len(values),
        }
        if numeric:
            stats["min"] = round(min(numeric), 4)
            stats["max"] = round(max(numeric), 4)
            stats["mean"] = round(sum(numeric) / len(numeric), 4)
        else:
            unique = list(dict.fromkeys(values))  # preserve order, deduplicate
            stats["unique_values"] = len(unique)
            stats["sample"] = unique[:5]

        summary["column_stats"][col] = stats

    return summary


def to_markdown(summary: dict[str, Any], source: str = "") -> str:
    """Render a summary dict as a Markdown report."""
    lines = ["# CSV Report"]
    if source:
        lines.append(f"\n**Source:** `{source}`")
    lines.append(f"**Total rows:** {summary['total_rows']}")
    lines.append(f"**Columns:** {', '.join(summary['columns'])}\n")

    lines.append("## Column Statistics\n")
    for col, stats in summary["column_stats"].items():
        lines.append(f"### `{col}`")
        lines.append(f"- Non-empty: {stats['non_empty']}")
        lines.append(f"- Empty: {stats['empty']}")
        if "mean" in stats:
            lines.append(f"- Min / Mean / Max: {stats['min']} / {stats['mean']} / {stats['max']}")
        else:
            lines.append(f"- Unique values: {stats['unique_values']}")
            lines.append(f"- Sample: {stats['sample']}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarise a CSV file.")
    parser.add_argument("csv_file", help="Path to input CSV file")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", help="Write output to this file (default: stdout)")
    args = parser.parse_args(argv)

    try:
        rows = load_csv(args.csv_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    summary = summarize(rows)

    if args.format == "json":
        output = json.dumps(summary, indent=2)
    else:
        output = to_markdown(summary, source=args.csv_file)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Report saved to: {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
