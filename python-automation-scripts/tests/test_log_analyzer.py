"""Tests for scripts/log_analyzer.py"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from log_analyzer import analyze_log, to_markdown, to_json, main


SAMPLE_LOG = """
2024-01-15 10:00:01 INFO  Application started
2024-01-15 10:00:02 DEBUG Loading configuration
2024-01-15 10:01:00 WARNING Disk usage above 80%
2024-01-15 10:02:00 ERROR  Failed to connect to database: timeout
2024-01-15 10:02:01 ERROR  Retrying connection (attempt 2)
2024-01-15 10:03:00 CRITICAL Unhandled exception in worker thread
2024-01-15 10:04:00 INFO  Recovery successful
"""


class TestAnalyzeLog:
    def test_total_lines(self):
        result = analyze_log(SAMPLE_LOG)
        assert result["total_lines"] == len(SAMPLE_LOG.splitlines())

    def test_counts_errors(self):
        result = analyze_log(SAMPLE_LOG)
        assert result["level_counts"].get("ERROR", 0) == 2

    def test_counts_critical(self):
        result = analyze_log(SAMPLE_LOG)
        assert result["level_counts"].get("CRITICAL", 0) == 1

    def test_counts_warnings(self):
        result = analyze_log(SAMPLE_LOG)
        assert result["level_counts"].get("WARNING", 0) == 1

    def test_min_level_filters(self):
        result = analyze_log(SAMPLE_LOG, min_level="ERROR")
        assert "WARNING" not in result["filtered_entries"]

    def test_warning_included_at_default_level(self):
        result = analyze_log(SAMPLE_LOG, min_level="WARNING")
        assert "WARNING" in result["filtered_entries"]

    def test_empty_log(self):
        result = analyze_log("")
        assert result["total_lines"] == 0
        assert result["level_counts"] == {}


class TestFormatters:
    def test_to_markdown_has_title(self):
        result = analyze_log(SAMPLE_LOG)
        md = to_markdown(result)
        assert "# Log Analysis Report" in md

    def test_to_markdown_has_table(self):
        result = analyze_log(SAMPLE_LOG)
        md = to_markdown(result)
        assert "| Level |" in md

    def test_to_json_valid(self):
        result = analyze_log(SAMPLE_LOG)
        data = json.loads(to_json(result))
        assert "total_lines" in data
        assert "level_counts" in data


class TestCli:
    def test_cli_runs(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("2024-01-01 INFO All good\n")
        ret = main([str(log)])
        assert ret == 0

    def test_cli_returns_1_on_errors(self, tmp_path):
        log = tmp_path / "err.log"
        log.write_text("2024-01-01 ERROR Something broke\n")
        ret = main([str(log)])
        assert ret == 1

    def test_cli_missing_file(self):
        ret = main(["no_such_file.log"])
        assert ret == 1
