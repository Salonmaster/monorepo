# 🧠 Application Architecture

Salonmaster runs as a single C++ Drogon binary — one process that handles auth, REST API, WebSocket connections, business logic, and background jobs.

---

## Single Binary, All Responsibilities

```
┌──────────────────────────────────────┐
│          Drogon HTTP Server           │
│                                      │
│  ┌────────┐  ┌────────┐  ┌────────┐ │
│  │  Auth  │  │  REST  │  │   WS   │ │
│  │ (JWT)  │  │  API   │  │ Server │ │
│  └────────┘  └────────┘  └────────┘ │
│                                      │
│  ┌────────────────────────────────┐  │
│  │     Business Logic Layer       │  │
│  │  Appointments · Clients · POS  │  │
│  │  Staff · Inventory · Reports   │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌──────────┐  ┌──────────────────┐  │
│  │ In-Proc  │  │  PostgreSQL      │  │
│  │ Job Queue│  │  (Drogon ORM)    │  │
│  └──────────┘  └──────────────────┘  │
│                                      │
│  ┌────────────────────────────────┐  │
│  │  Structured JSON logging       │  │
│  │  Prometheus /metrics endpoint  │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

---

## Why Monolith?

| Concern | Monolith Solution |
|---|---|
| **Hosting cost** | One binary, one process, one deployment. No service mesh overhead. |
| **Performance** | In-process calls, no network serialization between services. |
| **Auth** | Built-in JWT issuance and validation in Drogon filters. No Keycloak. |
| **Async jobs** | In-process queue for reminders, exports. No RabbitMQ. |
| **WebSocket** | Native Drogon WebSocket support. Multi-terminal sync. |
| **Simplicity** | One `Dockerfile`, one `docker-compose.yml`. Anyone can deploy it. |

---

## Request Flow

```
Client (Flutter) ──REST/WS──→ Drogon HTTP Server
                                │
                                ├── Auth Filter (JWT validate)
                                │
                                ├── Route → Controller → Business Logic
                                │       │
                                │       ├── Drogon ORM → PostgreSQL
                                │       │
                                │       └── Job Queue (in-proc)
                                │
                                └── Response (JSON or WS message)
```

---

## Multi-Tenancy

Tenant isolation happens at the database layer:

- **Schema-per-tenant** in PostgreSQL (`tenant_<slug>`)
- **JWT claims** carry tenant ID — enforced by auth filter
- **Connection pool** scoped per schema at query time
- No per-tenant deployments, no per-tenant pods

A single Drogon process serves all tenants. Scale up the VPS when needed, or add read replicas.

---

## Build & Packaging

- **C++23** with CMake and Conan dependency management
- **Size-optimized**: `-Os -ffunction-sections -fdata-sections -Wl,--gc-sections`
- **UPX compressed** binary
- **FROM scratch** Docker image — the binary is the only file
- Total image size: ~5MB

```bash
# Build
cmake --preset release
cmake --build --preset release

# Docker
docker build -t salonmaster-backend .
docker compose up -d
```

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Language | C++ | 23 |
| HTTP Framework | Drogon | latest |
| Serialization | glaze + jsoncpp | — |
| Database ORM | Drogon ORM (PostgreSQL) | — |
| Auth | Built-in JWT (HS256/RS256) | — |
| Logging | spdlog (structured JSON) | — |
| Metrics | Prometheus (Drogon plugin) | — |
| CLI | CLI11 | — |
