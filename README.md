# 💈 Salonmaster

Monorepo for the Salonmaster platform — a low-cost POS and management system for hair, nail, and beauty salons.

## Structure

```
├── Backend/       C++23 Drogon monolith (auth, API, WebSocket, business logic)
├── Client/        Flutter cross-platform app (iOS, Android, macOS, Linux)
├── Docs/          MkDocs documentation site
├── Kubernetes/    K8s deployment configs + Stylist CLI (scale path)
├── Terraform/     Hetzner Cloud infrastructure as code
└── Website/       Laravel marketing + booking site
```

## Stack

- **Backend:** C++23 Drogon → single binary, FROM scratch Docker image
- **Database:** PostgreSQL (self-hosted on same VPS)
- **Auth:** Built-in JWT (no external auth server)
- **Client:** Flutter (single codebase, all platforms)
- **Hosting:** €4/mo Hetzner VPS via Docker Compose
- **Scale path:** Kubernetes + Terraform when needed

## Branching

```
feat/*, fix/*, chore/*
        ↓
      main          ← acceptance/staging
        ↓
   tag: v1.0.0      ← production release
```

## Quick Start

```bash
# Backend
cd Backend
docker compose up -d

# Docs
cd Docs
poetry install && poetry run mkdocs serve

# Client
cd Client
flutter run
```

## Repositories

Previously split across 6 repos — now consolidated here.
# Build trigger test
# Webhook test 19:38:21
