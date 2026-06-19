# Developer Guide

## Prerequisites

- **C++23 compiler** (GCC 13+ or Clang 17+)
- **CMake 3.21+**
- **Conan 2** (C++ package manager)
- **PostgreSQL 16+** (for local dev)
- **Docker** (for containerized dev and deployment)
- **Python 3.12 + Poetry** (for docs tooling only)

## Quick Start

```bash
# Clone
git clone https://github.com/Salonmaster/Backend.git
cd Backend

# Install deps via Conan
conan profile detect --force
conan install . --build=missing -s build_type=Debug

# Build
cmake --preset debug
cmake --build --preset debug

# Run (with local PostgreSQL)
./build/Debug/Backend --config config.dev.json
```

## Docker Compose Dev

```bash
docker compose -f docker-compose.dev.yml up -d
# Starts: Backend + PostgreSQL + docs live server
```

## Project Structure

```
Backend/
├── src/
│   ├── main.cpp              # Entry point
│   ├── Application/          # Bootstrapper, globals
│   ├── Controllers/          # HTTP route handlers
│   ├── Middleware/            # Auth, logging, error handling
│   ├── Models/               # Database models (Drogon ORM)
│   ├── Schemas/              # JSON schemas (glaze)
│   ├── Helpers/              # Crypto, JWT, utilities
│   └── Types/                # Custom types
├── database/
│   └── migrations/           # SQL migration files
├── config.example.json       # Configuration template
├── Dockerfile                # Multi-stage FROM scratch build
└── docker-compose.yml        # Production deployment
```

## Branching

- `main` — production-ready
- `feature/<name>` — feature branches
- PR requires CI pass (build + tests)

## Testing

```bash
cmake --build --preset debug --target test
# Or with CTest:
ctest --preset debug
```

## Docs

```bash
cd ../Documentation
poetry install
poetry run mkdocs serve
# → http://localhost:8000
```

## Code Style

- C++23 with `-Wall -Wextra -Wpedantic`
- clang-format with project `.clang-format`
- Structured JSON logging via spdlog
- JWT auth on all routes except `/health` and `/metrics`
