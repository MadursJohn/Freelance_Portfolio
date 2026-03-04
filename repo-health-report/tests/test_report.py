"""Tests for src/report.py"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from datetime import datetime, timezone, timedelta
from metrics import RepoMetrics, CommitSummary
from report import to_markdown, to_html


def make_metrics(**overrides) -> RepoMetrics:
    recent = (datetime.now(tz=timezone.utc) - timedelta(days=5)).isoformat()
    defaults = dict(
        owner="alice",
        name="test-repo",
        full_name="alice/test-repo",
        description="A test repo",
        stars=10,
        forks=2,
        open_issues_count=1,
        open_prs_count=0,
        default_branch="main",
        language="Python",
        last_pushed_at=recent,
        created_at="2023-01-01T00:00:00Z",
        recent_commits=[
            CommitSummary(sha="abc1234", message="initial commit", author="Alice", date="2024-01-01T00:00:00Z")
        ],
    )
    defaults.update(overrides)
    return RepoMetrics(**defaults)


class TestToMarkdown:
    def test_has_title(self):
        md = to_markdown([make_metrics()])
        assert "# Repository Health Report" in md

    def test_contains_repo_name(self):
        md = to_markdown([make_metrics()])
        assert "alice/test-repo" in md

    def test_contains_language(self):
        md = to_markdown([make_metrics()])
        assert "Python" in md

    def test_multiple_repos(self):
        md = to_markdown([make_metrics(), make_metrics(name="other", full_name="alice/other")])
        assert "alice/test-repo" in md
        assert "alice/other" in md

    def test_includes_commit(self):
        md = to_markdown([make_metrics()])
        assert "initial commit" in md

    def test_empty_list(self):
        md = to_markdown([])
        assert "# Repository Health Report" in md


class TestToHtml:
    def test_is_html(self):
        html = to_html([make_metrics()])
        assert "<!DOCTYPE html>" in html
        assert "<table>" in html

    def test_contains_repo_name(self):
        html = to_html([make_metrics()])
        assert "alice/test-repo" in html

    def test_contains_github_link(self):
        html = to_html([make_metrics()])
        assert "https://github.com/alice/test-repo" in html
