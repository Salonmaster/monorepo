# Database

Salonmaster uses PostgreSQL with schema-per-tenant isolation. The database runs alongside the Drogon binary on the same VPS — no separate cluster, no managed service.

---

## Layout

- **PostgreSQL 16+** — self-hosted, included in `docker-compose.yml`
- **Schema naming**: `tenant_<slug>` per tenant
- **Extensions**: `uuid-ossp`, `pgcrypto`

## Why Self-Hosted?

| | Aurora (old) | Self-Hosted (new) |
|---|---|---|
| Monthly cost | $$$ per GB | €0 (on same VPS) |
| Latency | Network round-trip | Unix socket / localhost |
| Complexity | AWS account, VPC, IAM | One Docker container |
| Backup | PITR in S3 ($) | `pg_dump` cron to disk + rclone to Proton Drive |

For 50+ salons on a single VPS, self-hosted PostgreSQL is more than enough.

---

## Access Control

- Application connects via local Unix socket or `localhost`
- Schema-level `search_path` set per-request based on JWT tenant claim
- No PgBouncer needed at this scale (single binary, connection pooling built into Drogon)

## Migrations

- SQL migration files in `Backend/database/migrations/`
- Applied by Drogon on startup (configurable)
- Versioned, idempotent, reviewed in PRs

## Backups

- Nightly `pg_dump` per schema
- Compressed and uploaded to Proton Drive via rclone
- 30-day retention

## Related

- [Application Overview](../application/application.md)
- [Data Model](../product/data-model.md)
