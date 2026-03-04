# python-automation-scripts

> A collection of practical Python automation scripts with tests and CI — built
> for real-world tasks like data processing, API monitoring, and log analysis.

![CI](https://github.com/YOUR_USERNAME/python-automation-scripts/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Scripts

| Script | What it does | No external deps |
|--------|-------------|:---:|
| `csv_processor.py` | Validate, summarize, and report on any CSV file | ✅ |
| `api_health_check.py` | Ping HTTP endpoints and produce a health report | ✅ |
| `log_analyzer.py` | Scan log files for ERROR/WARNING patterns | ✅ |

All scripts use only the **Python standard library** — no pip installs needed to run them.

---

## Quick start

```bash
git clone https://github.com/YOUR_USERNAME/python-automation-scripts.git
cd python-automation-scripts

# Run any script directly — no install required
python scripts/csv_processor.py data.csv
python scripts/log_analyzer.py app.log --level ERROR
python scripts/api_health_check.py endpoints.json
```

### CSV Processor

```bash
python scripts/csv_processor.py my_data.csv --format markdown
python scripts/csv_processor.py my_data.csv --format json --output report.json
```

Output example:
```
# CSV Report
**Total rows:** 1500
**Columns:** id, name, revenue, region

## Column Statistics
### `revenue`
- Min / Mean / Max: 0.5 / 4823.1 / 98000.0
```

### API Health Check

Create an `endpoints.json`:
```json
[
    {"name": "Main API",    "url": "https://api.example.com/health"},
    {"name": "Auth Service","url": "https://auth.example.com/ping"}
]
```

Then run:
```bash
python scripts/api_health_check.py endpoints.json --timeout 5
```

Returns exit code `0` if all healthy, `1` if any endpoint is down — perfect for CI gates.

### Log Analyzer

```bash
python scripts/log_analyzer.py /var/log/app.log --level ERROR --format markdown
python scripts/log_analyzer.py app.log --tail 500   # last 500 lines only
```

---

## Running tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v --cov=scripts
```

---

## Structure

```
python-automation-scripts/
├── scripts/
│   ├── csv_processor.py      # CSV validation & reporting
│   ├── api_health_check.py   # HTTP endpoint monitoring
│   └── log_analyzer.py       # Log scanning & analysis
├── tests/
│   ├── test_csv_processor.py
│   └── test_log_analyzer.py
├── .github/workflows/ci.yml
└── requirements-dev.txt
```

---

## Why these scripts?

These automate three of the most common recurring tasks in any software team:

1. **CSV/data ingestion validation** — catch format issues before they reach production
2. **Health monitoring** — lightweight alternative to heavy monitoring suites for small projects
3. **Log triage** — quickly surface critical errors from noisy log files after a deployment

Each script outputs both **Markdown** (for reports/wikis) and **JSON** (for pipeline integration).

---

## License

MIT
