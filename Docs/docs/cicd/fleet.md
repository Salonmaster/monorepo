# GitOps with Rancher Fleet

Rancher Fleet continuously reconciles every Salonmaster environment. Git is the source of truth for cluster add-ons, platform services, and tenant-specific releases.

## Repository Layout

```
environments/
  prod/
    fleet.yaml
    tenants/
      tenant-a/
      tenant-b/
  staging/
    ...
charts/
  salonmaster/
  tenants/
```

- Each environment folder owns its Fleet bundle
- Tenants live under `environments/<env>/tenants/<tenant>` and reuse shared Helm charts

## Promotion Flow

1. Developers open a pull request modifying Helm values or tenant manifests
2. CI validates the bundles using `fleet validate` and unit tests
3. Once merged, Fleet detects the change and applies it to the cluster

## Operational Guidelines

- Keep bundles small so rollouts remain incremental
- Use Git tags or branches to represent release trains
- Document tenant overrides inside their folder with a `README.md` for clarity

## Related Documents

- [GitHub Actions Pipeline](github-actions.md)
- [Tenant Setup](../tenants/setup.md)
- [Cluster Architecture](../architecture/cluster.md)
