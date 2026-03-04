"""
formatter.py
------------
Convert a BuildResult into human-readable output formats:
Markdown table, plain text summary, and JSON.
"""

from __future__ import annotations

import json
from typing import Callable

from .parser import BuildResult, StepResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STATUS_ICON = {"passed": "✅", "failed": "❌", "skipped": "⏭️", "unknown": "❓"}


def _icon(status: str) -> str:
    return _STATUS_ICON.get(status, "❓")


def _fmt_seconds(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins}m {secs:.0f}s"


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def to_markdown(result: BuildResult) -> str:
    """Render *result* as a Markdown report suitable for GitHub PRs or wikis.

    Example output::

        ## Build Report

        | Step | Status | Duration | Errors |
        |------|--------|----------|--------|
        | Lint | ✅ passed | 4.2s | 0 |
        ...
    """
    lines = ["## Build Report", ""]

    overall_icon = _icon(result.overall_status)
    lines += [
        f"**Overall:** {overall_icon} `{result.overall_status.upper()}`  ",
        f"**Total duration:** {_fmt_seconds(result.total_duration_seconds)}  ",
        f"**Pass rate:** {result.pass_rate:.0f}% "
        f"({len(result.passed_steps)}/{len(result.steps)} steps)",
        "",
        "| Step | Status | Duration | Errors |",
        "|------|--------|----------|--------|",
    ]

    for step in result.steps:
        lines.append(
            f"| {step.name} "
            f"| {_icon(step.status)} {step.status} "
            f"| {_fmt_seconds(step.duration_seconds)} "
            f"| {len(step.errors)} |"
        )

    if result.failed_steps:
        lines += ["", "### ❌ Failures", ""]
        for step in result.failed_steps:
            lines.append(f"**{step.name}**")
            for err in step.errors:
                lines.append(f"```\n{err}\n```")

    return "\n".join(lines)


def to_text(result: BuildResult) -> str:
    """Render *result* as a plain-text summary (useful in terminal or logs)."""
    lines = [
        "=" * 50,
        f"BUILD {result.overall_status.upper()}",
        f"Duration : {_fmt_seconds(result.total_duration_seconds)}",
        f"Pass rate: {result.pass_rate:.0f}%",
        "-" * 50,
    ]
    for step in result.steps:
        icon = _icon(step.status)
        lines.append(
            f"  {icon}  {step.name:<30} {_fmt_seconds(step.duration_seconds):>8}"
        )
    lines.append("=" * 50)
    return "\n".join(lines)


def to_json(result: BuildResult) -> str:
    """Serialise *result* to a JSON string."""
    data = {
        "overall_status": result.overall_status,
        "total_duration_seconds": result.total_duration_seconds,
        "pass_rate": round(result.pass_rate, 1),
        "steps": [
            {
                "name": s.name,
                "status": s.status,
                "duration_seconds": s.duration_seconds,
                "errors": s.errors,
            }
            for s in result.steps
        ],
    }
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Format dispatcher
# ---------------------------------------------------------------------------

_FORMATTERS: dict[str, Callable[[BuildResult], str]] = {
    "markdown": to_markdown,
    "text": to_text,
    "json": to_json,
}


def format_result(result: BuildResult, fmt: str = "markdown") -> str:
    """Dispatch to the correct formatter by name.

    Parameters
    ----------
    result:
        Parsed build result.
    fmt:
        One of ``"markdown"``, ``"text"``, ``"json"``.

    Raises
    ------
    ValueError
        If *fmt* is not a recognised format name.
    """
    if fmt not in _FORMATTERS:
        raise ValueError(f"Unknown format '{fmt}'. Choose from: {list(_FORMATTERS)}")
    return _FORMATTERS[fmt](result)
