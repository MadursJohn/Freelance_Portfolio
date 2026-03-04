"""Tests for scripts/csv_processor.py"""

import json
import os
import tempfile
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from csv_processor import load_csv, summarize, to_markdown, main


SAMPLE_CSV_CONTENT = """name,age,city
Alice,30,London
Bob,25,Porto
Carol,35,Berlin
Dave,,London
"""

NUMERIC_CSV = """product,price,quantity
Widget,1.99,100
Gadget,9.99,50
Doohickey,0.50,200
"""


@pytest.fixture
def sample_csv(tmp_path):
    p = tmp_path / "sample.csv"
    p.write_text(SAMPLE_CSV_CONTENT, encoding="utf-8")
    return str(p)


@pytest.fixture
def numeric_csv(tmp_path):
    p = tmp_path / "numeric.csv"
    p.write_text(NUMERIC_CSV, encoding="utf-8")
    return str(p)


class TestLoadCsv:
    def test_returns_list_of_dicts(self, sample_csv):
        rows = load_csv(sample_csv)
        assert isinstance(rows, list)
        assert isinstance(rows[0], dict)

    def test_correct_row_count(self, sample_csv):
        rows = load_csv(sample_csv)
        assert len(rows) == 4

    def test_column_names_correct(self, sample_csv):
        rows = load_csv(sample_csv)
        assert set(rows[0].keys()) == {"name", "age", "city"}

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            load_csv("nonexistent.csv")

    def test_empty_file_raises(self, tmp_path):
        p = tmp_path / "empty.csv"
        p.write_text("")
        with pytest.raises(ValueError):
            load_csv(str(p))


class TestSummarize:
    def test_total_rows(self, sample_csv):
        rows = load_csv(sample_csv)
        s = summarize(rows)
        assert s["total_rows"] == 4

    def test_columns_present(self, sample_csv):
        rows = load_csv(sample_csv)
        s = summarize(rows)
        assert "name" in s["columns"]
        assert "age" in s["columns"]

    def test_empty_count(self, sample_csv):
        rows = load_csv(sample_csv)
        s = summarize(rows)
        assert s["column_stats"]["age"]["empty"] == 1

    def test_numeric_stats_computed(self, numeric_csv):
        rows = load_csv(numeric_csv)
        s = summarize(rows)
        price_stats = s["column_stats"]["price"]
        assert "min" in price_stats
        assert "max" in price_stats
        assert "mean" in price_stats
        assert price_stats["min"] == pytest.approx(0.50)
        assert price_stats["max"] == pytest.approx(9.99)

    def test_text_column_has_unique_count(self, sample_csv):
        rows = load_csv(sample_csv)
        s = summarize(rows)
        assert "unique_values" in s["column_stats"]["city"]


class TestToMarkdown:
    def test_contains_header(self, sample_csv):
        rows = load_csv(sample_csv)
        md = to_markdown(summarize(rows))
        assert "# CSV Report" in md

    def test_contains_column_names(self, sample_csv):
        rows = load_csv(sample_csv)
        md = to_markdown(summarize(rows))
        assert "name" in md
        assert "age" in md


class TestCli:
    def test_cli_runs_markdown(self, sample_csv):
        ret = main([sample_csv, "--format", "markdown"])
        assert ret == 0

    def test_cli_runs_json(self, sample_csv, tmp_path):
        out = str(tmp_path / "out.json")
        ret = main([sample_csv, "--format", "json", "--output", out])
        assert ret == 0
        data = json.loads(open(out).read())
        assert "total_rows" in data

    def test_cli_missing_file(self):
        ret = main(["does_not_exist.csv"])
        assert ret == 1
