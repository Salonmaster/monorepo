# Product Architecture

How product components map to the low-cost monolith stack.

![Global System Diagram](../assets/diagrams/salonmaster-global.drawio)

[Edit in diagrams.net →](https://app.diagrams.net)

---

## Component Stack

```
┌──────────────────────────────────────────┐
│           CLIENT LAYER                   │
│  Flutter App (iOS · Android · Desktop)   │
│  Laravel Website (Marketing + Booking)   │
├──────────────────────────────────────────┤
│        DROGON MONOLITH (C++23)           │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐  │
│  │ JWT Auth │ │ REST API │ │  WS API │  │
│  └──────────┘ └──────────┘ └─────────┘  │
│  ┌────────────────────────────────────┐  │
│  │        Business Logic              │  │
│  │  Appointments · Clients · POS      │  │
│  │  Staff · Inventory · Reports       │  │
│  └────────────────────────────────────┘  │
│  ┌──────────────┐ ┌──────────────────┐   │
│  │ In-Proc Jobs │ │ Drogon ORM       │   │
│  └──────────────┘ └──────────────────┘   │
├──────────────────────────────────────────┤
│           DATA LAYER                     │
│  PostgreSQL (self-hosted) — per-tenant   │
│  Proton Drive — backups                  │
├──────────────────────────────────────────┤
│        INFRASTRUCTURE                    │
│  Hetzner VPS · Docker Compose             │
│  K8s + Terraform (scale path)             │
└──────────────────────────────────────────┘
```

---

## Client Architecture

![Client Architecture](../assets/diagrams/salonmaster-client.drawio)

[Edit in diagrams.net →](https://app.diagrams.net)

Flutter PWA-style app with offline SQLite, WebSocket sync, and JWT auth.

---

## Core Business Flow

![Core Flow](../assets/diagrams/salonmaster-core-flow.drawio)

[Edit in diagrams.net →](https://app.diagrams.net)

Booking → Appointment → Service Delivery → Checkout → Payment → History.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| C++ Drogon monolith | Single binary, tiny footprint, €4 VPS |
| Built-in JWT auth | No Keycloak — saves 512MB RAM and a Java VM |
| In-process job queue | No RabbitMQ — saves 200MB RAM |
| Self-hosted PostgreSQL | No Aurora markup — runs on same VPS |
| Flutter all platforms | Single codebase, zero hosting cost |
| Docker Compose deploy | One command, no cluster needed |
| K8s available for scale | Full Helm charts ready when needed |
