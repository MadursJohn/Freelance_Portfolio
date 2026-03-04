"""Tests for build_report.formatter"""

import json
import pytest
from build_report.parser import parse_log
from build_report.formatter import to_markdown, to_text, to_json, format_result


SAMPLE_LOG = """
[STEP]: Lint
PASSED in 3.2s

[STEP]: Unit Tests
PASSED in 12.5s

[STEP]: Build
FAILED in 5.1s
ERROR: package build failed
"""


@pytest.fixture
def build_result():
    return parse_log(SAMPLE_LOG)


class TestToMarkdown:
    def test_contains_header(self, build_result):
        md = to_markdown(build_result)
        assert "## Build Report" in md

    def test_contains_overall_status(self, build_result):
        md = to_markdown(build_result)
        assert "FAILED" in md

    def test_contains_table(self, build_result):
        md = to_markdown(build_result)
        assert "| Step |" in md

    def test_contains_step_names(self, build_result):
        md = to_markdown(build_result)
        assert "Lint" in md
        assert "Build" in md

    def test_failures_section_present(self, build_result):
        md = to_markdown(build_result)
        assert "Failures" in md

    def test_pass_rate_shown(self, build_result):
        md = to_markdown(build_result)
        assert "%" in md


class TestToText:
    def test_contains_build_status(self, build_result):
        txt = to_text(build_result)
        assert "FAILED" in txt

    def test_contains_step_names(self, build_result):
        txt = to_text(build_result)
        assert "Lint" in txt

    def test_separator_present(self, build_result):
        txt = to_text(build_result)
        assert "=" in txt


class TestToJson:
    def test_valid_json(self, build_result):
        js = to_json(build_result)
        data = json.loads(js)  # must not raise
        assert isinstance(data, dict)

    def test_json_contains_steps(self, build_result):
        js = to_json(build_result)
        data = json.loads(js)
        assert "steps" in data
        assert len(data["steps"]) == 3

    def test_json_overall_status(self, build_result):
        js = to_json(build_result)
        data = json.loads(js)
        assert data["overall_status"] == "failed"


class TestFormatDispatcher:
    def test_markdown_dispatch(self, build_result):
        result = format_result(build_result, "markdown")
        assert "## Build Report" in result

    def test_text_dispatch(self, build_result):
        result = format_result(build_result, "text")
        assert "BUILD" in result

    def test_json_dispatch(self, build_result):
        result = format_result(build_result, "json")
        json.loads(result)  # valid JSON

    def test_unknown_format_raises(self, build_result):
        with pytest.raises(ValueError, match="Unknown format"):
            format_result(build_result, "xml")
