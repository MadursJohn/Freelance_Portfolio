"""
metrics.py
----------
Transform raw GitHub API responses into a clean RepoMetrics dataclass
suitable for rendering into reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass
class CommitSummary:
    sha: str
    message: str  # first line only
    author: str
    date: str


@dataclass
class RepoMetrics:
    """All metrics collected for one repository."""

    owner: str
    name: str
    full_name: str
    description: str
    stars: int
    forks: int
    open_issues_count: int
    open_prs_count: int
    default_branch: str
    language: str
    last_pushed_at: str
    created_at: str
    recent_commits: List[CommitSummary] = field(default_factory=list)

    @property
    def days_since_push(self) -> int | None:
        """Number of days since the last push."""
        if not self.last_pushed_at:
            return None
        try:
            pushed = datetime.fromisoformat(self.last_pushed_at.replace("Z", "+00:00"))
            delta = datetime.now(tz=timezone.utc) - pushed
            return delta.days
        except ValueError:
            return None

    @property
    def health_status(self) -> str:
        """Simple traffic-light status based on activity and open issues."""
        days = self.days_since_push
        if days is None:
            return "unknown"
        if days > 180:
            return "stale"
        if self.open_issues_count > 20:
            return "needs-attention"
        return "healthy"


def build_metrics(
    repo_data: dict,
    issues: list[dict],
    prs: list[dict],
    commits: list[dict],
) -> RepoMetrics:
    """Convert raw GitHub API dicts into a :class:`RepoMetrics` object.

    Parameters
    ----------
    repo_data:
        Response from ``GET /repos/{owner}/{repo}``.
    issues:
        List of open issues (pull_requests already filtered out).
    prs:
        List of open pull requests.
    commits:
        List of recent commit objects.
    """
    recent = []
    for c in commits[:5]:
        raw_msg = c.get("commit", {}).get("message", "")
        first_line = raw_msg.splitlines()[0] if raw_msg else ""
        author = (
            c.get("commit", {}).get("author", {}).get("name", "")
            or c.get("author", {}).get("login", "unknown")
        )
        date = c.get("commit", {}).get("author", {}).get("date", "")
        recent.append(CommitSummary(sha=c["sha"][:7], message=first_line, author=author, date=date))

    parts = repo_data.get("full_name", "/").split("/")
    owner = parts[0] if len(parts) > 1 else ""

    return RepoMetrics(
        owner=owner,
        name=repo_data.get("name", ""),
        full_name=repo_data.get("full_name", ""),
        description=repo_data.get("description") or "",
        stars=repo_data.get("stargazers_count", 0),
        forks=repo_data.get("forks_count", 0),
        open_issues_count=len(issues),
        open_prs_count=len(prs),
        default_branch=repo_data.get("default_branch", "main"),
        language=repo_data.get("language") or "N/A",
        last_pushed_at=repo_data.get("pushed_at", ""),
        created_at=repo_data.get("created_at", ""),
        recent_commits=recent,
    )
