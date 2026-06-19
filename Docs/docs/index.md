# 💈 Salonmaster — Low-Cost POS for Beauty Salons

**Salonmaster** is a lean, high-performance Point of Sale and management platform for hair, nail, and beauty salons. One C++ binary, one database, one VPS — designed to keep hosting costs near zero.

---

## ✨ Why Salonmaster?

- 💶 **€4/mo hosting** — single Drogon C++ binary + PostgreSQL on a Hetzner VPS serves 50+ salons
- ⚡ **Sub-millisecond responses** — C++23 Drogon with `-Os` optimizations, UPX-compressed `FROM scratch` Docker image
- 📱 **Flutter clients** — iOS, Android, macOS, Linux from one codebase, runs on staff devices (€0 hosting)
- 🔐 **Built-in JWT auth** — no separate Keycloak server, no Java overhead
- 📴 **Offline-capable** — Flutter client syncs when Wi-Fi returns, salon keeps running
- 📊 **Schema-per-tenant PostgreSQL** — strong data isolation without extra services
- 🐳 **Docker Compose first** — one command to deploy, K8s available when you need scale

---

## 🧱 The Stack

```
┌─────────────────────────────────────┐
│         HETZNER CX22 (€4/mo)        │
│                                     │
│  ┌───────────────────────────────┐  │
│  │   C++ Drogon Binary     20MB │  │
│  │   Auth · API · WS · Logic    │  │
│  │   In-process job queue       │  │
│  └───────────────────────────────┘  │
│                 ↕                    │
│  ┌───────────────────────────────┐  │
│  │   PostgreSQL           200MB  │  │
│  │   Schema-per-tenant           │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
          ↑ REST + WebSocket
    ┌─────┴─────┐
    │  Flutter   │  ← iOS, Android, macOS, Linux
    │  ClientV2  │     Zero hosting cost
    └───────────┘
```

| Layer | Technology | Hosting |
|---|---|---|
| Backend | C++23 Drogon (single binary) | €4 VPS |
| Database | PostgreSQL (self-hosted) | Included |
| Auth | Built-in JWT (no Keycloak) | Included |
| Async | In-process queue (no RabbitMQ) | Included |
| Client | Flutter | €0 (on devices) |
| Website | Laravel | €0 (Cloudflare Pages) |
| **Total** | | **~€4/mo** |

---

## 🗺️ Repository Map

| Repo | Purpose |
|---|---|
| [Backend](https://github.com/Salonmaster/Backend) | C++ Drogon monolith — everything |
| [ClientV2](https://github.com/Salonmaster/ClientV2) | Flutter cross-platform app |
| [Website](https://github.com/Salonmaster/Website) | Laravel marketing + booking site |
| [Kubernetes](https://github.com/Salonmaster/Kubernetes) | K8s configs (scale path) |
| [Terraform-Hetzner](https://github.com/Salonmaster/Terraform-Hetzner) | Infrastructure as Code |
| [Documentation](https://github.com/Salonmaster/Documentation) | This site |

Archived: `Server`, `Client`, `Protocol`, `ProtocolV2`, `REST-API`

---

## 📚 Documentation

- 📦 [**Architecture**](architecture/cluster.md) — System design and networking
- 🔧 [**Application**](application/application.md) — Backend monolith deep-dive
- 🗄 [**Database**](app/database.md) — Schema design and tenancy
- 📊 [**Monitoring**](monitoring/grafana.md) — Metrics, logs, alerts
- 🚀 [**Deployment**](deployment/docker-compose.md) — Get running in 5 minutes
- 💻 [**Product**](product/index.md) — Features, plan, modules
- 🛠 [**Developer Guide**](developer-guide.md) — Contributing
