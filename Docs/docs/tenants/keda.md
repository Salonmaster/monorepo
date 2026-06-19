# ⚖️ KEDA Autoscaling

This document describes how Salonmaster uses **KEDA (Kubernetes Event-Driven Autoscaling)** to scale workloads based on demand, with a focus on per-tenant isolation.

---

## 🚀 Purpose

Salonmaster is built to support a multi-tenant architecture where each tenant's workload can scale independently. KEDA enables the platform to:

- Scale tenant **worker pods** based on RabbitMQ queue depth
- Scale tenant **API pods** based on:
  - Scheduled triggers
  - KEDA Gateway HTTP requests
  - RabbitMQ activity (optional)

This ensures that:

- Idle tenants consume no resources
- Busy tenants scale responsively and independently

---

## 🏗️ Per-Tenant Scaling Architecture

Each tenant resides in its own Kubernetes namespace, with dedicated scaling components:

- **ScaledObjects** for queue-based or external triggers
- **HorizontalPodAutoscaler (HPA)** for CPU/memory scaling
- API deployments that support scale-to-zero recovery
- Worker deployments strictly tied to message queue depth

> All scaling definitions are declared via Helm values and deployed via GitOps (Fleet).

---

## 🐇 Worker Autoscaling (RabbitMQ)

Worker pods are scaled solely by RabbitMQ queue length:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: worker-autoscaler
  namespace: tenant42
spec:
  scaleTargetRef:
    name: worker
  triggers:
    - type: rabbitmq
      metadata:
        queueName: tasks-tenant42
        host: amqp://user:pass@rabbitmq.core.svc.cluster.local/
        queueLength: "10"
```

---

## 🧠 API Autoscaling

The API pods support multiple triggers:

### 1. Scheduled Activation

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: api-scheduler
  namespace: tenant42
spec:
  scaleTargetRef:
    name: api
  triggers:
    - type: cron
      metadata:
        timezone: Europe/Amsterdam
        start: "0 7 * * *"
        end: "0 22 * * *"
        desiredReplicas: "1"
```

### 2. HTTP Gateway Trigger

When scaled to 0, requests via Cloudflare hit the **KEDA Gateway**, which:

- Triggers scale-up of the target API deployment
- Waits for readiness
- Proxies the request onward

This flow enables **cold-start recovery without 502s**.

### 3. Optional RabbitMQ Trigger

Some tenants may scale API pods on queue depth (e.g., webhook or job handlers).

---

## 🔍 Observability

KEDA emits metrics collected via Prometheus:

- `keda_scaled_object_queue_length`
- `keda_scaled_object_replicas`
- `keda_trigger_value`

Dashboards are tenant-aware in Grafana.

---

## 🔁 Autoscaling Flow Diagram

```mermaid
%%{ init: { "themeVariables": { "fontFamily": "Inter, Roboto, sans-serif", "primaryColor": "#F48FB1", "edgeLabelBackground": "#ffffff", "background": "transparent" } } }%%
graph TD
  subgraph External
    CF[Cloudflare] --> GW[KEDA Gateway]
    GW --> APITrigger[Trigger API Deployment]
  end

  subgraph Tenant_Namespace
    API[API Deployment]
    Worker
    APICron[ScaledObject: Schedule]
    WorkerScaler[ScaledObject: RabbitMQ]
  end

  subgraph Shared_RabbitMQ_Namespace
    RabbitMQ  --> WorkerScaler[ScaledObject: RabbitMQ]
  end
  
  WorkerScaler --> |Request Scale| KEDA[KEDA Controller]
  APICron --> |Request Scale| KEDA
  APITrigger --> |Request Scale| KEDA
  KEDA -->|Scale| API
  KEDA -->|Scale| Worker
```

---

## ✅ Summary

- **Worker pods**: scaled only by RabbitMQ queue
- **API pods**: scaled by cron, KEDA gateway, and optionally queue
- Scale-to-zero support is fully automated
- KEDA is integrated with Prometheus/Grafana for observability

---

## 🔗 Related Docs

- [Tenant Setup](setup.md)
- [Cluster Architecture](../architecture/cluster.md)
- [Networking](../architecture/networking.md)
- [Monitoring](../monitoring/grafana.md)

