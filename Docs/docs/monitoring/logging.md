# Logging Pipeline

Application and platform logs are centralized through Fluent Bit and Elasticsearch. Structured JSON events ensure fields remain queryable for every tenant.

## Flow

1. Pods emit JSON logs to stdout
2. Fluent Bit enriches them with namespace, pod, and tenant labels
3. Logs are shipped to Elasticsearch with daily index rotation
4. Kibana dashboards and saved searches expose tenant views

## Retention and Privacy

- Default retention: 30 days in hot storage, 180 days in warm tier
- PII is minimized at source and redacted when necessary using Fluent Bit filters
- Tenants can export their own logs through signed URLs

## Operational Runbooks

- When ingestion lags, scale Fluent Bit and Elasticsearch ingest nodes
- For query slowness, run index lifecycle management (ILM) to move cold shards to cheaper storage
- Use Kibana alerting to detect spikes in error logs per tenant

## Related Documents

- [Monitoring and Dashboards](grafana.md)
- [Alerting](alerts.md)
- [Security](../architecture/security.md)
