# Frequently Asked Questions

### How do I add a new tenant?
Create a tenant folder under the Fleet environment, provide Helm values, and merge the change. Fleet applies the namespace, secrets, and workloads automatically.

### Does each tenant run its own database?
No. Tenants share a PostgreSQL cluster but receive isolated schemas with scoped credentials. This keeps operational cost low while preserving isolation.

### Can tenants scale independently?
Yes. KEDA watches per-tenant metrics and scales API or worker deployments based on demand. Idle tenants scale to zero.

### Where can I see logs and metrics?
Log in to Grafana for dashboards and to Kibana for log searches. Both tools support tenant filters based on namespace labels.

### How are deployments approved?
All changes flow through pull requests. GitHub Actions validates code, and Fleet applies manifests only after they reach the `main` branch.
