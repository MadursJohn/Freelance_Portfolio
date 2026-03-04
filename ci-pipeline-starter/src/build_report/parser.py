"""
parser.py
---------
Parse raw CI build log text into a structured BuildResult dataclass.

Handles common patterns found in Jenkins, GitHub Actions, and similar
CI systems: step names, durations, pass/fail outcomes, and error lines.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class StepResult:
    """Represents a single step (stage) in a CI build log."""

    name: str
    status: str  # "passed" | "failed" | "skipped"
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class BuildResult:
    """Aggregated result parsed from a full CI build log."""

    steps: List[StepResult] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    overall_status: str = "unknown"  # "passed" | "failed" | "unknown"

    @property
    def passed_steps(self) -> List[StepResult]:
        return [s for s in self.steps if s.status == "passed"]

    @property
    def failed_steps(self) -> List[StepResult]:
        return [s for s in self.steps if s.status == "failed"]

    @property
    def pass_rate(self) -> float:
        """Return percentage of steps that passed (0-100)."""
        if not self.steps:
            return 0.0
        return (len(self.passed_steps) / len(self.steps)) * 100


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_STEP_START = re.compile(r"^\[(STEP|STAGE|RUN)\]\s*[:\-]\s*(.+)", re.IGNORECASE)
_STEP_PASS = re.compile(r"\b(PASSED|SUCCESS|OK)\b", re.IGNORECASE)
_STEP_FAIL = re.compile(r"\b(FAILED|ERROR|FAILURE)\b", re.IGNORECASE)
_DURATION = re.compile(r"(\d+(?:\.\d+)?)\s*s(?:ec(?:onds?)?)?", re.IGNORECASE)
_ERROR_LINE = re.compile(r"^\s*(ERROR|CRITICAL|FATAL)\b.+", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_log(log_text: str) -> BuildResult:
    """Parse a raw build log string and return a :class:`BuildResult`.

    Parameters
    ----------
    log_text:
        Raw text content of the CI build log.

    Returns
    -------
    BuildResult
        Structured representation of the build outcome.
    """
    result = BuildResult()
    current_step: StepResult | None = None

    for line in log_text.splitlines():
        # Detect step/stage start
        step_match = _STEP_START.match(line)
        if step_match:
            if current_step:
                result.steps.append(current_step)
            current_step = StepResult(name=step_match.group(2).strip(), status="unknown")
            continue

        if current_step is None:
            continue

        # Detect outcome
        if _STEP_PASS.search(line):
            current_step.status = "passed"
        elif _STEP_FAIL.search(line):
            current_step.status = "failed"

        # Detect duration
        dur_match = _DURATION.search(line)
        if dur_match:
            current_step.duration_seconds = float(dur_match.group(1))

        # Collect error lines
        if _ERROR_LINE.match(line):
            current_step.errors.append(line.strip())

    # Append last step
    if current_step:
        result.steps.append(current_step)

    # Compute totals
    result.total_duration_seconds = sum(s.duration_seconds for s in result.steps)
    if any(s.status == "failed" for s in result.steps):
        result.overall_status = "failed"
    elif result.steps:
        result.overall_status = "passed"

    return result


def parse_log_file(path: str) -> BuildResult:
    """Convenience wrapper — read a log file from *path* and parse it."""
    with open(path, encoding="utf-8") as fh:
        return parse_log(fh.read())
