"""
log_analyzer.py
---------------
Scan a log file for ERROR, WARNING, and CRITICAL entries.
Groups them by level, counts occurrences, and produces a summary.

Supports common log formats (plain text lines with timestamps).

Usage:
    python log_analyzer.py app.log
    python log_analyzer.py app.log --level ERROR --format json
    python log_analyzer.py app.log --tail 100   # analyze only last N lines
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_LEVEL_PATTERN = re.compile(
    r"\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b", re.IGNORECASE
)
_TIMESTAMP_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
)

LEVEL_PRIORITY = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "WARN": 2,
    "ERROR": 3,
    "CRITICAL": 4,
    "FATAL": 4,
}


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def analyze_log(
    text: str,
    min_level: str = "WARNING",
) -> dict:
    """Analyse *text* and return a structured summary dict.

    Parameters
    ----------
    text:
        Raw log file content.
    min_level:
        Only include entries at this level or higher.
    """
    min_priority = LEVEL_PRIORITY.get(min_level.upper(), 2)

    level_counts: Counter = Counter()
    level_lines: dict[str, list[str]] = defaultdict(list)
    total_lines = 0

    for line in text.splitlines():
        total_lines += 1
        match = _LEVEL_PATTERN.search(line)
        if not match:
            continue
        level = match.group(1).upper()
        if level == "WARN":
            level = "WARNING"
        if level == "FATAL":
            level = "CRITICAL"
        priority = LEVEL_PRIORITY.get(level, 0)
        level_counts[level] += 1
        if priority >= min_priority:
            level_lines[level].append(line.strip())

    return {
        "total_lines": total_lines,
        "level_counts": dict(level_counts),
        "filtered_entries": {
            level: lines for level, lines in level_lines.items()
        },
        "min_level_filter": min_level.upper(),
    }


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def to_markdown(summary: dict, source: str = "") -> str:
    lines = ["# Log Analysis Report"]
    if source:
        lines.append(f"\n**Source:** `{source}`")

    lines += [
        f"**Total lines:** {summary['total_lines']}",
        f"**Min level filter:** `{summary['min_level_filter']}`",
        "",
        "## Level Counts",
        "",
        "| Level | Count |",
        "|-------|-------|",
    ]
    for level, count in sorted(
        summary["level_counts"].items(),
        key=lambda x: LEVEL_PRIORITY.get(x[0], 0),
        reverse=True,
    ):
        lines.append(f"| {level} | {count} |")

    for level, entries in summary["filtered_entries"].items():
        if entries:
            lines += ["", f"## {level} Entries ({len(entries)} total)", ""]
            for entry in entries[:20]:  # cap at 20 to keep readable
                lines.append(f"```\n{entry}\n```")
            if len(entries) > 20:
                lines.append(f"*... and {len(entries) - 20} more.*")

    return "\n".join(lines)


def to_json(summary: dict) -> str:
    return json.dumps(summary, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze a log file for issues.")
    parser.add_argument("log_file", help="Path to log file")
    parser.add_argument(
        "--level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Minimum log level to include (default: WARNING)",
    )
    parser.add_argument("--tail", type=int, help="Only analyze last N lines")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", help="Write report to file")
    args = parser.parse_args(argv)

    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"ERROR: File not found: {log_path}", file=sys.stderr)
        return 1

    text = log_path.read_text(encoding="utf-8", errors="replace")
    if args.tail:
        text = "\n".join(text.splitlines()[-args.tail:])

    summary = analyze_log(text, min_level=args.level)

    if args.format == "markdown":
        output = to_markdown(summary, source=args.log_file)
    else:
        output = to_json(summary)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Report saved: {args.output}")
    else:
        print(output)

    has_errors = summary["level_counts"].get("ERROR", 0) + summary["level_counts"].get("CRITICAL", 0)
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
