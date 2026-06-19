# Alerting Strategy

Alerting ensures platform issues surface quickly without overwhelming operators. Alertmanager receives signals from Prometheus, Elasticsearch, and synthetic checks, then fans them out to Slack, PagerDuty, and email as required.

## Alert Classes

- **Availability**: API latency, error rates, ingress health
- **Scalability**: Queue depth, KEDA failures, replica shortages
- **Security**: Unexpected namespace creations, auth anomalies, failed logins

## Workflow

1. Prometheus records rules evaluate metrics and fire alerts
2. Alertmanager groups by severity and tenant, then routes to the correct team
3. Runbooks linked in alerts point back to this documentation set

## Noise Reduction

- Use inhibition rules so dependent alerts do not duplicate noise
- Tune recording rules with moving averages to avoid flapping
- Provide tenant metadata in annotations to speed up triage

## Related Documents

- [Monitoring and Dashboards](grafana.md)
- [Logging Pipeline](logging.md)
- [Security](../architecture/security.md)
