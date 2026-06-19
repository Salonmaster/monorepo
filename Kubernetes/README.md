# Kubernetes Platform Toolkit

[![Python Tests](https://github.com/Salonmaster/Kubernetes/actions/workflows/python-tests.yml/badge.svg?branch=tst)](https://github.com/Salonmaster/Kubernetes/actions/workflows/python-tests.yml)
[![Coverage & Platform CI](https://github.com/Salonmaster/Kubernetes/actions/workflows/platform-ci.yml/badge.svg?branch=tst)](https://github.com/Salonmaster/Kubernetes/actions/workflows/platform-ci.yml)
[![CodeQL](https://github.com/Salonmaster/Kubernetes/actions/workflows/github-code-scanning/codeql/badge.svg?branch=tst)](https://github.com/Salonmaster/Kubernetes/actions/workflows/github-code-scanning/codeql)

Infrastructure-as-code for the Salonmaster platform. This repository combines a GitOps-friendly Helm catalog with the **Stylist** automation CLI so you can bootstrap, operate, and recycle entire Kubernetes environments with a single command.

## Highlights

- **App of Apps GitOps** – Argo CD drives every workload via the manifests in `app-of-apps/` and `apps/`.
- **Stylist CLI** – Opinionated automation for bootstrapping clusters, seeding Vault secrets, rotating databases, and inspecting health.
- **Batteries-included CI** – Dedicated workflows run Helm linting, Trivy scans, Python tests, and coverage publishing on every push or pull request.

## Repository Layout

| Path | Purpose |
| ---- | ------- |
| `app-of-apps/` | Argo CD umbrella app that wires every workload together. |
| `apps/` | Individual Helm charts (Argo CD, Vault, Keycloak, monitoring stack, etc.). |
| `stylist/` | Typer-based CLI, helper modules, and tests that orchestrate installs/resets. |
| `stylist/tests/` | Pytest suite, helper stubs, and coverage configuration. |
| `.github/workflows/` | Automation for Helm security scans, Python tests, Stylist smoke tests, and full platform CI. |

## Quick Start

1. **Clone and enter the repo**
   ```bash
   git clone git@github.com:Salonmaster/Kubernetes.git
   cd Kubernetes
   ```
2. **Install tooling** – Helm, kubectl, Poetry, and Argo CD CLI.
3. **Install Python deps**
   ```bash
   poetry install
   ```
4. **Configure Stylist** – Copy `.env.sample` to `.env` (or export env vars) with your kubeconfig, Vault, and database settings.
5. **Bootstrap a cluster**
   ```bash
   poetry run python stylist/main.py cluster bootstrap
   ```
6. **Inspect or tear down**
   ```bash
   poetry run python stylist/main.py cluster status
   poetry run python stylist/main.py cluster info
   poetry run python stylist/main.py cluster reset
   ```

Stylist automatically seeds secrets, installs Helm repositories, deploys Argo CD, and finally applies the App of Apps manifest so every downstream chart comes online.

## Working With Helm Apps

- Each directory under `apps/` is a self-contained chart with its own `Chart.yaml`, templates, and env-specific values (`values-*.yaml`).
- Update chart versions or values locally, then let Argo CD reconcile the change through the GitOps flow.
- Add a new workload by scaffolding a Helm chart under `apps/` and referencing it from the App of Apps manifest.

## Local Development, Tests, and Coverage

- Run the Stylist unit suite with coverage:
  ```bash
  poetry run pytest --cov=stylist --cov-report=term-missing
  ```
- `python-tests.yml` executes the same command on every push/PR, while `platform-ci.yml` runs the end-to-end pipeline, publishes a coverage summary, and uploads `coverage.xml` for downstream tools.
- Coverage data feeds the badge above and is archived as a workflow artifact so historical reports remain accessible. For a snapshot of the latest local run, see [docs/coverage-report.md](docs/coverage-report.md).

## Environment Configuration

- Stylist reads `.env` automatically; any value can also be provided via CLI flags or real environment variables.
- Refer to [stylist/README.md](stylist/README.md) for the full command reference, subcommand help text, and advanced examples (database editors, proxy helpers, etc.).

## Automated Checks

- [.github/workflows/helm-security.yml](.github/workflows/helm-security.yml) keeps Helm dependencies fresh, lints charts, and scans manifests with Trivy.
- [.github/workflows/stylist.yml](.github/workflows/stylist.yml) exercises the CLI against a mocked environment to catch regressions early.
- Status for every workflow is visible via the badges at the top of this file.

## Commit Message Convention

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification. Commit messages are automatically linted on pull requests and pushes to main branches.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring without feature changes or bug fixes
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Changes to build system or dependencies
- `ci`: Changes to CI configuration files and scripts
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit
- `helm`: Changes to Helm charts
- `k8s`: Kubernetes-specific changes

### Examples

```
feat(website): add user authentication
fix(database): resolve connection pool timeout
docs: update installation instructions
helm(monitoring): upgrade Prometheus to v2.45.0
ci: add commitlint workflow
```

### Local Setup

To lint commit messages locally:

```bash
poetry install --only dev
poetry run cz check --rev-range HEAD~1..HEAD
```

Or to check the last commit:

```bash
poetry run cz check
```

You can also use commitizen to create properly formatted commits interactively:

```bash
poetry run cz commit
```

## Contributing

Issues and pull requests are welcome. Please open a discussion before large refactors so we can keep Stylist automation and Helm charts aligned.

## License

MIT License. See [LICENSE](LICENSE) for details.
