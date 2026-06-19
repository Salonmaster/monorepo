# GitHub Actions Pipeline

GitHub Actions orchestrates Salonmaster builds, tests, and documentation publishing. Workflows run inside the `.github/workflows` directory and are designed to be deterministic and cache-friendly.

## Key Workflows

- `docs.yml`: builds MkDocs with Poetry and deploys to GitHub Pages
- `backend.yml`: compiles API and worker containers, runs unit tests, and pushes images to ECR
- `tenant-validation.yml`: renders Helm values for every tenant to ensure manifests stay valid

## Best Practices

- Pin every action version using commit SHAs or major tags
- Reuse composite actions for common tasks such as Poetry setup or AWS authentication
- Enforce required status checks on the `main` branch before merging

## Secrets Management

- Store AWS credentials, container registry tokens, and other secrets in GitHub Environments
- Prefer OpenID Connect roles instead of long-lived access keys whenever AWS supports it

## Related Documents

- [GitOps with Fleet](fleet.md)
- [Developer Guide](../developer-guide.md)
- [Security](../architecture/security.md)
