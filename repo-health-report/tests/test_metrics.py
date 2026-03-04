"""Tests for src/metrics.py"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from metrics import build_metrics, RepoMetrics


REPO_DATA = {
    "full_name": "alice/my-repo",
    "name": "my-repo",
    "description": "A test repo",
    "stargazers_count": 42,
    "forks_count": 7,
    "default_branch": "main",
    "language": "Python",
    "pushed_at": "2024-01-10T12:00:00Z",
    "created_at": "2023-01-01T00:00:00Z",
}

COMMITS = [
    {
        "sha": "abc123def456",
        "commit": {
            "message": "fix: handle edge case\nMore details here",
            "author": {"name": "Alice", "date": "2024-01-10T11:00:00Z"},
        },
        "author": {"login": "alice"},
    }
]


class TestBuildMetrics:
    def test_returns_repo_metrics(self):
        m = build_metrics(REPO_DATA, [], [], COMMITS)
        assert isinstance(m, RepoMetrics)

    def test_name_parsed(self):
        m = build_metrics(REPO_DATA, [], [], [])
        assert m.name == "my-repo"
        assert m.owner == "alice"

    def test_stars_and_forks(self):
        m = build_metrics(REPO_DATA, [], [], [])
        assert m.stars == 42
        assert m.forks == 7

    def test_open_issues_count(self):
        pseudo_issues = [{}, {}, {}]
        m = build_metrics(REPO_DATA, pseudo_issues, [], [])
        assert m.open_issues_count == 3

    def test_open_prs_count(self):
        pseudo_prs = [{}, {}]
        m = build_metrics(REPO_DATA, [], pseudo_prs, [])
        assert m.open_prs_count == 2

    def test_commit_message_first_line_only(self):
        m = build_metrics(REPO_DATA, [], [], COMMITS)
        assert m.recent_commits[0].message == "fix: handle edge case"

    def test_commit_sha_shortened(self):
        m = build_metrics(REPO_DATA, [], [], COMMITS)
        assert m.recent_commits[0].sha == "abc123d"

    def test_language(self):
        m = build_metrics(REPO_DATA, [], [], [])
        assert m.language == "Python"


class TestRepoMetricsProperties:
    def test_days_since_push_is_int(self):
        m = build_metrics(REPO_DATA, [], [], [])
        assert isinstance(m.days_since_push, int)

    def test_health_status_stale_if_old(self):
        old_repo = {**REPO_DATA, "pushed_at": "2020-01-01T00:00:00Z"}
        m = build_metrics(old_repo, [], [], [])
        assert m.health_status == "stale"

    def test_health_status_healthy_recent(self):
        from datetime import datetime, timezone, timedelta
        recent = (datetime.now(tz=timezone.utc) - timedelta(days=10)).isoformat()
        new_repo = {**REPO_DATA, "pushed_at": recent}
        m = build_metrics(new_repo, [], [], [])
        assert m.health_status == "healthy"

    def test_invalid_date_returns_none(self):
        bad_repo = {**REPO_DATA, "pushed_at": "not-a-date"}
        m = build_metrics(bad_repo, [], [], [])
        assert m.days_since_push is None
