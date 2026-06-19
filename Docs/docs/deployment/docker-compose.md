# Deployment

Salonmaster is designed to be the cheapest SaaS you can run. One command gets you live.

---

## Production: Docker Compose

```bash
git clone https://github.com/Salonmaster/Backend.git
cd Backend
cp config.example.json config.json
# Edit config.json with your settings
docker compose up -d
```

That's it. Backend + PostgreSQL running on your VPS.

### docker-compose.yml

```yaml
services:
  backend:
    build: .
    ports:
      - "80:8080"
    volumes:
      - ./config.json:/app/config.json:ro
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: salonmaster
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: salonmaster
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U salonmaster"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  pgdata:
```

---

## VPS Sizing

| Provider | Plan | vCPU | RAM | Price | Capacity |
|---|---|---|---|---|---|
| Hetzner | CX22 | 1 | 2GB | €3.99/mo | ~50 salons |
| Hetzner | CX32 | 2 | 4GB | €7.99/mo | ~200 salons |
| Hetzner | CX42 | 4 | 8GB | €15.99/mo | ~500+ salons |

Start with CX22. Scale vertically first (bigger VPS), then horizontally when needed.

---

## Backups

Add to crontab on the VPS:

```bash
# Nightly backup at 3 AM
0 3 * * * docker exec salonmaster-postgres pg_dump -U salonmaster salonmaster | gzip > /backups/salonmaster-$(date +\%Y\%m\%d).sql.gz

# Upload to Proton Drive
0 4 * * * rclone copy /backups/ proton:SalonMaster/Backups/
```

---

## Monitoring

The Drogon binary exposes:

- `GET /health` — liveness check
- `GET /metrics` — Prometheus metrics

Point any Prometheus + Grafana instance at it, or use the built-in `drogon::plugin::PromExporter`.

---

## Scale Path

When you outgrow a single VPS:

1. **Read replica** — add PostgreSQL replica for read-heavy workloads
2. **Multiple backend instances** — load balance with nginx/HAProxy
3. **K8s** — existing `Kubernetes` repo has full Helm charts, Rancher Fleet, KEDA autoscaling
4. **Multi-region** — Terraform-Hetzner configs ready

But don't start here. A CX22 will take you far.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `postgres` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_USER` | `salonmaster` | Database user |
| `DB_PASSWORD` | — | Database password |
| `DB_NAME` | `salonmaster` | Database name |
| `JWT_SECRET` | — | HMAC secret for JWT signing |
| `LOG_LEVEL` | `info` | spdlog level |
| `PORT` | `8080` | HTTP listen port |
