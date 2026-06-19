# 🧩 Multi-Tenant Setup

This guide outlines how new tenants are provisioned in Salonmaster, including namespace creation, schema isolation, messaging, and API gateway configuration.

---

## 🏗️ Tenant Architecture

Each tenant gets a fully isolated logical environment within the cluster. The key building blocks include:

| Layer      | Isolation Mechanism         |
| ---------- | --------------------------- |
| Kubernetes | Dedicated namespace         |
| PostgreSQL | Per-tenant schema           |
| RabbitMQ   | Per-tenant queues           |
| Networking | Ingress + hostname routing  |
| Scaling    | KEDA autoscalers per tenant |

> Tenants do not share deployments or data paths. Observability is labeled and scoped per tenant.

---

## 🛠️ Provisioning Steps

Tenant onboarding is done declaratively via GitOps (Rancher Fleet). The flow:

1. **Create a Helm values file** for the new tenant (e.g. `tenants/tenant42.yaml`)
2. Define:
   - Namespace: `tenant42`
   - Database schema: `tenant42`
   - Queue name(s): `tasks-tenant42`
   - Subdomain: `tenant42.salonhub.io`
3. Push to Git — Fleet deploys:
   - Namespace & RBAC
   - API & Worker deployments
   - ScaledObjects (KEDA)
   - NetworkPolicy (optional)

---

## 🗃️ Database Schema

- All tenants use the same Aurora PostgreSQL database instance
- Each tenant has its own **dedicated schema**
- Role-based access ensures apps can only reach their own schema

Schema is auto-provisioned by a post-deployment job (e.g. Alembic or Prisma migration).

---

## 🐇 Message Queues

RabbitMQ is shared but logically partitioned:

- Each tenant gets dedicated queues like `tasks-tenant42`
- Workers are scoped to only listen to those queues
- KEDA monitors queue depth for scaling

---

## 🌐 Subdomain Routing

- Each tenant is assigned a unique subdomain: `tenantXYZ.salonhub.io`
- All ingress traffic routes through Cloudflare Tunnel
- API traffic passes through the **KEDA-aware gateway** to trigger scale-up if needed

---

## 🧼 Cleanup & Offboarding

To remove a tenant:

- Remove their Helm values file
- Commit and push to Git
- Fleet will delete all associated K8s resources

Database schema and queue data must be manually reviewed and deleted.

---

## 📄 Example Helm Values (Partial)

```yaml
tenant:
  name: tenant42
  namespace: tenant42
  subdomain: tenant42.salonhub.io
  dbSchema: tenant42
  queueName: tasks-tenant42
```

---

## 🧠 Summary

- Tenants are isolated across all infra layers
- Onboarding is fully GitOps-driven
- Cloudflare + KEDA ensure zero-pod responsiveness
- Database and messaging are shared but securely partitioned

---

## 🔗 Related Docs

- [KEDA Autoscaling](keda.md)
- [Cluster Architecture](../architecture/cluster.md)
- [Networking](../architecture/networking.md)

