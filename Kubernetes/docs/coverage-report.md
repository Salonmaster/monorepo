# Coverage Report

_Last updated: 2025-12-18 via `poetry run pytest --cov=stylist --cov-report=term`._

| Metric | Value |
| ------ | ----- |
| Total statements | 2,360 |
| Missed statements | 1,345 |
| Total branches | 522 |
| Partial branches | 42 |
| Overall coverage | **38%** |

## Module Snapshot

| Module (top-level) | Coverage |
| ------------------ | -------- |
| `stylist/__init__.py` | 90% |
| `stylist/commands/*` | 29–100% (see CLI table below) |
| `stylist/helpers/database.py` | 78% |
| `stylist/helpers/remote_db.py` | 91% |
| `stylist/helpers/cluster.py` | 11% |
| `stylist/core/*` | 12–100% |
| `stylist/console/*` | 0–39% |

> The full raw table is produced automatically by the pytest coverage plugin and can be reproduced locally with:
>
> ```bash
> poetry run pytest --cov=stylist --cov-report=term-missing
> ```

Future CI runs in `platform-ci.yml` also upload `coverage.xml`, which downstream tools (Codecov, Sonar, etc.) can consume for deeper analysis.
