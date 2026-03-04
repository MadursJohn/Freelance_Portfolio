"""
github_client.py
----------------
Minimal GitHub REST API v3 client using only the standard library.
Fetches repository metadata, open issues, pull requests, and recent commits.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

BASE_URL = "https://api.github.com"


class GitHubClient:
    """Lightweight GitHub API v3 client.

    Parameters
    ----------
    token:
        GitHub personal access token.  If omitted, the ``GITHUB_TOKEN``
        environment variable is used.  Unauthenticated requests are rate-limited
        to 60/hour; a token raises the limit to 5 000/hour.
    """

    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.getenv("GITHUB_TOKEN", "")

    def _get(self, path: str, params: dict | None = None) -> Any:
        """Make a GET request to the GitHub API and return parsed JSON."""
        url = f"{BASE_URL}{path}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "repo-health-report/1.0",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            raise RuntimeError(f"GitHub API error {exc.code}: {body}") from exc

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_repo(self, owner: str, repo: str) -> dict:
        """Return repository metadata (stars, forks, open issues, etc.)."""
        return self._get(f"/repos/{owner}/{repo}")

    def get_open_issues(self, owner: str, repo: str) -> list[dict]:
        """Return all open issues (excluding pull requests)."""
        items = self._get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": "open", "per_page": "100"},
        )
        # GitHub issues endpoint also returns PRs; filter them out
        return [i for i in items if "pull_request" not in i]

    def get_open_pull_requests(self, owner: str, repo: str) -> list[dict]:
        """Return all open pull requests."""
        return self._get(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": "open", "per_page": "100"},
        )

    def get_recent_commits(self, owner: str, repo: str, count: int = 10) -> list[dict]:
        """Return the *count* most recent commits on the default branch."""
        return self._get(
            f"/repos/{owner}/{repo}/commits",
            params={"per_page": str(count)},
        )
