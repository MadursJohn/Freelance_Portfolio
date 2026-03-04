"""Tests for build_report.parser"""

import pytest
from build_report.parser import parse_log, BuildResult, StepResult


SAMPLE_LOG = """
[STEP]: Lint
Running flake8...
PASSED in 3.2s

[STEP]: Unit Tests
Running pytest...
PASSED in 12.5s

[STEP]: Build
Building package...
PASSED in 5.1s
"""

FAILING_LOG = """
[STEP]: Lint
Running flake8...
PASSED in 2.1s

[STEP]: Unit Tests
Running pytest...
ERROR: test_something.py::test_broken - AssertionError
FAILED in 8.3s
"""


class TestParseLog:
    def test_returns_build_result(self):
        result = parse_log(SAMPLE_LOG)
        assert isinstance(result, BuildResult)

    def test_detects_all_steps(self):
        result = parse_log(SAMPLE_LOG)
        assert len(result.steps) == 3

    def test_step_names_parsed_correctly(self):
        result = parse_log(SAMPLE_LOG)
        names = [s.name for s in result.steps]
        assert "Lint" in names
        assert "Unit Tests" in names
        assert "Build" in names

    def test_all_passed_status(self):
        result = parse_log(SAMPLE_LOG)
        assert all(s.status == "passed" for s in result.steps)

    def test_overall_status_passed(self):
        result = parse_log(SAMPLE_LOG)
        assert result.overall_status == "passed"

    def test_durations_parsed(self):
        result = parse_log(SAMPLE_LOG)
        durations = {s.name: s.duration_seconds for s in result.steps}
        assert durations["Lint"] == pytest.approx(3.2)
        assert durations["Unit Tests"] == pytest.approx(12.5)

    def test_total_duration_computed(self):
        result = parse_log(SAMPLE_LOG)
        assert result.total_duration_seconds == pytest.approx(3.2 + 12.5 + 5.1)

    def test_failed_step_detected(self):
        result = parse_log(FAILING_LOG)
        failed = result.failed_steps
        assert len(failed) == 1
        assert failed[0].name == "Unit Tests"

    def test_overall_status_failed(self):
        result = parse_log(FAILING_LOG)
        assert result.overall_status == "failed"

    def test_error_lines_captured(self):
        result = parse_log(FAILING_LOG)
        failed_step = result.failed_steps[0]
        assert len(failed_step.errors) > 0

    def test_empty_log_returns_unknown(self):
        result = parse_log("")
        assert result.overall_status == "unknown"
        assert result.steps == []

    def test_pass_rate_all_pass(self):
        result = parse_log(SAMPLE_LOG)
        assert result.pass_rate == pytest.approx(100.0)

    def test_pass_rate_partial(self):
        result = parse_log(FAILING_LOG)
        assert result.pass_rate == pytest.approx(50.0)  # 1/2 steps passed

    def test_passed_steps_property(self):
        result = parse_log(SAMPLE_LOG)
        assert len(result.passed_steps) == 3

    def test_failed_steps_property_empty_on_success(self):
        result = parse_log(SAMPLE_LOG)
        assert result.failed_steps == []
