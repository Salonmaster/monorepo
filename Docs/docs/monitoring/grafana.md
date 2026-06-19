# Monitoring and Dashboards

Salonmaster consolidates metrics and tracing inside a shared observability stack. Each tenant's workloads include namespace labels so aggregates remain filterable and auditable.

## Stack Components

- Prometheus for scraping pod metrics, KEDA stats, and RabbitMQ exporters
- Grafana for dashboards covering API latency, worker throughput, and database health
- Alertmanager for routing incidents to on-call channels

## Dashboard Strategy

1. Global overview dashboard summarizes platform health
2. Tenant drill-down dashboard filters by namespace labels
3. SLO dashboard monitors request latency and error budgets

## Operations

- Dashboards are stored as JSON manifests in Git and synced via Grafana provisioning
- Alerts include runbook links that live in this documentation set
- Synthetic checks exercise public endpoints through Cloudflare to validate ingress

## Related Documents

- [Logging Pipeline](logging.md)
- [Alerting](alerts.md)
- [Cluster Architecture](../architecture/cluster.md)
