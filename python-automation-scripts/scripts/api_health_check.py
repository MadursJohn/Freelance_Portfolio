"""
api_health_check.py
-------------------
Check the health of a list of HTTP endpoints and produce a status report.
Useful for monitoring services, validating deployments, or integration tests.

Usage:
    python api_health_check.py endpoints.json
    python api_health_check.py endpoints.json --timeout 5 --format markdown

endpoints.json format:
    [
        {"name": "Main API", "url": "https://api.example.com/health"},
        {"name": "Auth Service", "url": "https://auth.example.com/ping", "expected_status": 200}
    ]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class EndpointResult:
    name: str
    url: str
    status_code: int | None = None
    response_time_ms: float = 0.0
    healthy: bool = False
    error: str = ""


@dataclass
class HealthReport:
    results: List[EndpointResult] = field(default_factory=list)

    @property
    def healthy_count(self) -> int:
        return sum(1 for r in self.results if r.healthy)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def all_healthy(self) -> bool:
        return self.healthy_count == self.total


# ---------------------------------------------------------------------------
# Core checker
# ---------------------------------------------------------------------------


def check_endpoint(
    name: str,
    url: str,
    expected_status: int = 200,
    timeout: float = 10.0,
) -> EndpointResult:
    """Perform a GET request and return an :class:`EndpointResult`."""
    result = EndpointResult(name=name, url=url)
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "health-check/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result.status_code = resp.status
            result.healthy = resp.status == expected_status
    except urllib.error.HTTPError as exc:
        result.status_code = exc.code
        result.healthy = exc.code == expected_status
        result.error = str(exc)
    except Exception as exc:  # noqa: BLE001
        result.error = str(exc)
        result.healthy = False
    finally:
        result.response_time_ms = (time.perf_counter() - start) * 1000
    return result


def run_checks(
    endpoints: list[dict],
    timeout: float = 10.0,
) -> HealthReport:
    """Run health checks for all *endpoints* and return a :class:`HealthReport`."""
    report = HealthReport()
    for ep in endpoints:
        result = check_endpoint(
            name=ep.get("name", ep["url"]),
            url=ep["url"],
            expected_status=ep.get("expected_status", 200),
            timeout=timeout,
        )
        report.results.append(result)
    return report


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


_ICON = {True: "✅", False: "❌"}


def to_markdown(report: HealthReport) -> str:
    status = "HEALTHY" if report.all_healthy else "DEGRADED"
    icon = _ICON[report.all_healthy]
    lines = [
        f"# API Health Report — {icon} {status}",
        "",
        f"**{report.healthy_count}/{report.total}** endpoints healthy",
        "",
        "| Endpoint | URL | Status | Response Time | Healthy |",
        "|----------|-----|--------|---------------|---------|",
    ]
    for r in report.results:
        code = str(r.status_code) if r.status_code else "N/A"
        t = f"{r.response_time_ms:.0f} ms"
        lines.append(f"| {r.name} | {r.url} | {code} | {t} | {_ICON[r.healthy]} |")

    unhealthy = [r for r in report.results if not r.healthy]
    if unhealthy:
        lines += ["", "## ❌ Issues", ""]
        for r in unhealthy:
            lines.append(f"**{r.name}**: {r.error or 'unexpected status'}")
    return "\n".join(lines)


def to_json(report: HealthReport) -> str:
    return json.dumps(
        {
            "all_healthy": report.all_healthy,
            "healthy": report.healthy_count,
            "total": report.total,
            "results": [
                {
                    "name": r.name,
                    "url": r.url,
                    "status_code": r.status_code,
                    "response_time_ms": round(r.response_time_ms, 1),
                    "healthy": r.healthy,
                    "error": r.error,
                }
                for r in report.results
            ],
        },
        indent=2,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check API endpoint health.")
    parser.add_argument("endpoints_file", help="JSON file listing endpoints to check")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout (seconds)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", help="Write report to file instead of stdout")
    args = parser.parse_args(argv)

    ep_file = Path(args.endpoints_file)
    if not ep_file.exists():
        print(f"ERROR: File not found: {ep_file}", file=sys.stderr)
        return 1

    endpoints = json.loads(ep_file.read_text(encoding="utf-8"))
    report = run_checks(endpoints, timeout=args.timeout)

    output = to_markdown(report) if args.format == "markdown" else to_json(report)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Report saved: {args.output}")
    else:
        print(output)

    return 0 if report.all_healthy else 1


if __name__ == "__main__":
    sys.exit(main())
