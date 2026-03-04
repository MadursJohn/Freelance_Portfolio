"""
report.py
---------
Render a list of RepoMetrics objects into a Markdown or HTML report.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from metrics import RepoMetrics

_HEALTH_ICON = {"healthy": "🟢", "needs-attention": "🟡", "stale": "🔴", "unknown": "⚪"}


def to_markdown(metrics_list: List[RepoMetrics]) -> str:
    """Render metrics as a Markdown report."""
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Repository Health Report",
        "",
        f"*Generated: {now}*",
        f"*Repositories tracked: {len(metrics_list)}*",
        "",
        "## Summary",
        "",
        "| Repo | Status | Stars | Forks | Open Issues | Open PRs | Language | Last Push |",
        "|------|--------|-------|-------|-------------|----------|----------|-----------|",
    ]

    for m in metrics_list:
        icon = _HEALTH_ICON.get(m.health_status, "⚪")
        days = m.days_since_push
        push_str = f"{days}d ago" if days is not None else "unknown"
        url = f"https://github.com/{m.full_name}"
        lines.append(
            f"| [{m.full_name}]({url}) "
            f"| {icon} {m.health_status} "
            f"| {m.stars} "
            f"| {m.forks} "
            f"| {m.open_issues_count} "
            f"| {m.open_prs_count} "
            f"| {m.language} "
            f"| {push_str} |"
        )

    lines += ["", "---", "", "## Details", ""]

    for m in metrics_list:
        url = f"https://github.com/{m.full_name}"
        icon = _HEALTH_ICON.get(m.health_status, "⚪")
        lines += [
            f"### {icon} [{m.full_name}]({url})",
            "",
            f"> {m.description or 'No description.'}",
            "",
            f"- **Stars:** {m.stars}  |  **Forks:** {m.forks}  "
            f"|  **Language:** {m.language}",
            f"- **Main branch:** `{m.default_branch}`",
            f"- **Open issues:** {m.open_issues_count}  "
            f"|  **Open PRs:** {m.open_prs_count}",
            (
                f"- **Last push:** {m.last_pushed_at} ({m.days_since_push}d ago)"
                if m.days_since_push is not None
                else f"- **Last push:** {m.last_pushed_at}"
            ),
            "",
        ]

        if m.recent_commits:
            lines += ["**Recent commits:**", ""]
            for c in m.recent_commits:
                lines.append(f"- `{c.sha}` {c.message}  _{c.author}, {c.date[:10]}_")
            lines.append("")

    return "\n".join(lines)


def to_html(metrics_list: List[RepoMetrics]) -> str:
    """Render metrics as a self-contained HTML page."""
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows = ""
    for m in metrics_list:
        color = {"healthy": "#28a745", "needs-attention": "#ffc107",
                 "stale": "#dc3545", "unknown": "#6c757d"}.get(m.health_status, "#6c757d")
        days = f"{m.days_since_push}d ago" if m.days_since_push is not None else "unknown"
        url = f"https://github.com/{m.full_name}"
        rows += f"""
        <tr>
            <td><a href="{url}" target="_blank">{m.full_name}</a></td>
            <td><span style="color:{color};font-weight:bold">{m.health_status}</span></td>
            <td>{m.stars}</td>
            <td>{m.forks}</td>
            <td>{m.open_issues_count}</td>
            <td>{m.open_prs_count}</td>
            <td>{m.language}</td>
            <td>{days}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Repository Health Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1200px; margin: 40px auto; padding: 0 20px; color: #333; }}
    h1 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
    th, td {{ text-align: left; padding: 10px 14px; border-bottom: 1px solid #eee; }}
    th {{ background: #f8f9fa; font-weight: 600; }}
    tr:hover {{ background: #f8f9fa; }}
    a {{ color: #0366d6; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .meta {{ color: #6c757d; font-size: 0.9em; margin-bottom: 20px; }}
  </style>
</head>
<body>
  <h1>Repository Health Report</h1>
  <p class="meta">Generated: {now} &nbsp;|&nbsp; {len(metrics_list)} repositories</p>
  <table>
    <thead>
      <tr>
        <th>Repository</th><th>Status</th><th>Stars</th><th>Forks</th>
        <th>Open Issues</th><th>Open PRs</th><th>Language</th><th>Last Push</th>
      </tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>
</body>
</html>"""
