# repo-health-report

> Automatically fetch GitHub repository metrics and generate a Markdown + HTML
> health dashboard — rebuilt weekly by a scheduled GitHub Actions workflow.

![CI](https://github.com/YOUR_USERNAME/repo-health-report/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**[→ View the live report](HEALTH_REPORT.md)**

---

## What this does

1. Reads a `config.json` file listing GitHub repositories
2. Calls the **GitHub REST API** to collect: stars, forks, open issues, open PRs, recent commits
3. Computes a **health status** (🟢 healthy / 🟡 needs-attention / 🔴 stale) per repo
4. Generates a report in **Markdown** and **HTML**
5. A **scheduled GitHub Actions workflow** re-runs this every Monday and commits the updated report automatically

This demonstrates:
- GitHub REST API integration (no third-party libraries)
- Data aggregation and business logic (`metrics.py`)
- Multi-format report generation (`report.py`)
- Scheduled automation with GitHub Actions

---

## Quick start

```bash
git clone https://github.com/YOUR_USERNAME/repo-health-report.git
cd repo-health-report

# Edit config.json to list the repos you want to track
# Then run:

GITHUB_TOKEN=your_token_here python run_report.py config.json
# or on Windows:
# set GITHUB_TOKEN=your_token_here
# python run_report.py config.json

# Output formats
python run_report.py config.json --format markdown
python run_report.py config.json --format html --output report.html
```

---

## Configuration

Edit `config.json`:

```json
{
  "repositories": [
    { "owner": "microsoft", "repo": "vscode" },
    { "owner": "pallets",   "repo": "flask" },
    { "owner": "YOUR_USERNAME", "repo": "ci-pipeline-starter" }
  ]
}
```

---

## How the scheduled automation works

The workflow in `.github/workflows/ci.yml` has a `schedule` trigger:

```yaml
schedule:
  - cron: "0 8 * * 1"   # Every Monday at 08:00 UTC
```

On each run it:
1. Runs all tests ✅
2. Calls the GitHub API for every repo in `config.json`
3. Writes `HEALTH_REPORT.md` and `HEALTH_REPORT.html`
4. Commits and pushes the updated files automatically

No manual work needed — the report stays fresh with zero maintenance.

---

## Running tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v --cov=src
```

---

## Project structure

```
repo-health-report/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI + scheduled report generation
├── src/
│   ├── github_client.py        # GitHub REST API client (stdlib only)
│   ├── metrics.py              # Data model + health scoring
│   └── report.py               # Markdown & HTML renderers
├── tests/
│   ├── test_metrics.py
│   └── test_report.py
├── run_report.py               # CLI entry point
├── config.json                 # Repos to track
├── HEALTH_REPORT.md            # Auto-generated report (committed by CI)
└── HEALTH_REPORT.html          # Auto-generated HTML report
```

---

## No external dependencies

The core tool uses **only the Python standard library**: `urllib`, `json`, `dataclasses`.
Dev dependencies (`pytest`, `flake8`) are only needed for running tests.

---

## License

MIT
