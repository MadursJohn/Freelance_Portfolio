"""
run_report.py
-------------
CLI entry point for repo-health-report.

Usage:
    python run_report.py config.json --format markdown
    python run_report.py config.json --format html --output report.html
    GITHUB_TOKEN=ghp_xxx python run_report.py config.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# src/ is next to this file
sys.path.insert(0, str(Path(__file__).parent / "src"))

from github_client import GitHubClient  # noqa: E402
from metrics import build_metrics  # noqa: E402
from report import to_markdown, to_html  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a GitHub repo health report.")
    parser.add_argument("config", help="JSON config file listing repos to track")
    parser.add_argument("--format", choices=["markdown", "html"], default="markdown")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--token", help="GitHub token (overrides GITHUB_TOKEN env var)")
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}", file=sys.stderr)
        return 1

    config = json.loads(config_path.read_text(encoding="utf-8"))
    repos = config.get("repositories", [])

    if not repos:
        print("ERROR: No repositories listed in config.", file=sys.stderr)
        return 1

    # Owner resolution priority:
    #   1. per-entry "owner" field
    #   2. GITHUB_REPOSITORY_OWNER env var  (set automatically by GitHub Actions)
    #   3. top-level "default_owner" in config  (for local runs)
    env_owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
    default_owner = config.get("default_owner", "")

    client = GitHubClient(token=args.token)
    all_metrics = []

    for repo_spec in repos:
        name = repo_spec["repo"]
        owner = repo_spec.get("owner") or env_owner or default_owner
        if not owner:
            print(f"  ERROR: No owner resolved for repo '{name}'. "
                  "Set GITHUB_REPOSITORY_OWNER or add 'default_owner' to config.",
                  file=sys.stderr)
            continue
        print(f"  Fetching {owner}/{name} ...", file=sys.stderr)
        try:
            repo_data = client.get_repo(owner, name)
            issues = client.get_open_issues(owner, name)
            prs = client.get_open_pull_requests(owner, name)
            commits = client.get_recent_commits(owner, name)
            all_metrics.append(build_metrics(repo_data, issues, prs, commits))
        except RuntimeError as exc:
            print(f"  WARNING: Could not fetch {owner}/{name}: {exc}", file=sys.stderr)

    if not all_metrics:
        print("ERROR: Failed to fetch any repository data.", file=sys.stderr)
        return 1

    output = to_html(all_metrics) if args.format == "html" else to_markdown(all_metrics)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Report saved: {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
