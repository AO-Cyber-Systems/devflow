# PRD-011: DevFlow Runtime

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)  
**Investment:** $1.15M over 24 months (excluding Analytics)

---

## Executive Summary

DevFlow Runtime is a comprehensive backend platform that combines the power of Supabase (database, auth, storage) with a Heroku-style application deployment system. It provides a complete "Data + Deploy" solution where developers can push code and have it automatically built, deployed, and connected to managed infrastructure without configuration.

**Key Innovation**: Merging backend-as-a-service (Supabase) with platform-as-a-service (Deployment) into a single unified runtime where application code and database live together seamlessly.

---

## Goals

### Primary Goals

1. **Complete Backend Platform**: Provide database, auth, storage, and realtime capabilities out-of-the-box
2. **Zero-Config Deployment**: "Git push" deployment for any language/framework using buildpacks
3. **Automatic Infrastructure**: Auto-provisioning of databases and injection of connection strings
4. **Data Sovereignty**: Fully self-hosted architecture with no external dependencies
5. **Unified Observability**: Metrics, logs, and traces integrated into a single dashboard

### Secondary Goals

1. Serverless edge functions (compatible with Deno/Supabase)
2. Background worker system for async tasks
3. Scheduled jobs (cron) management
4. Custom domain management with automatic SSL
5. Vertical and horizontal auto-scaling

---

## Investment Breakdown

**Total**: $1.15M over 24 months

| Component | Cost | Duration | Priority |
|-----------|------|----------|----------|
| Supabase Core Integration | $450k | 15 months | P0 |
| App Deployment Engine | $100k | 8 months | P0 |
| Observability Stack | $120k | 4 months | P0 |
| Vespa Search Integration | $100k | 4 months | P1 |
| Neo4j Graph Integration | $80k | 3 months | P1 |
| Stripe Billing Engine | $40k | 2 months | P1 |
| Unified SDK | $50k | 2 months | P1 |
| Platform Polish | $210k | Ongoing | P2 |

**Timeline**:
- Month 1-6: Supabase Core (DB, Auth) + Basic Deployment
- Month 7-12: Advanced Deployment + Storage + Realtime
- Month 13-18: Observability + Search + Graph
- Month 19-24: Billing + SDK + Polish

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      DevFlow Runtime                             │
│                   ($1.15M over 24 months)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Backend    │    │  Deployment  │    │ Observability│
│  Services    │    │    Engine    │    │    Stack     │
│  (Supabase)  │    │              │    │              │
├──────────────┤    ├──────────────┤    ├──────────────┤
│ - PostgreSQL │    │ - Buildpacks │    │ - Prometheus │
│ - GoTrue     │    │ - OCI Images │    │ - Grafana    │
│ - Storage    │    │ - Kubernetes │    │ - Loki       │
│ - Realtime   │    │ - Ingress    │    │ - Tempo      │
│ - Edge Func  │    │ - Scaling    │    │ - Sentry     │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌──────────────────┐
                    │ Platform Services│
                    │                  │
                    ├──────────────────┤
                    │ - Vespa Search   │
                    │ - Neo4j Graph    │
                    │ - Stripe Billing │
                    │ - Redis Queue    │
                    └──────────────────┘
```

---

## Architecture Strategy

### Hybrid Multi-Project Isolation

DevFlow Runtime adopts the "Hybrid" isolation model (referencing Supabase's multi-project analysis) to balance security with resource efficiency:

1.  **Database-Per-Project**: Each project gets its own logical database within a shared PostgreSQL instance (or cluster). This ensures strong data isolation.
2.  **Shared Service Pools**: Stateless services (GoTrue, Realtime, Storage API) are pooled and shared across projects to minimize resource overhead.
3.  **Project-Aware Routing**: The API Gateway (Kong) routes requests to the correct database connection pool based on project ID.

### Deployment Modes

- **SaaS**: Fully managed, multi-tenant architecture with strict resource limits and billing integration.
- **On-Premise (Enterprise)**: Same architecture as SaaS, deployable via Kubernetes (Helm) or Docker Compose for smaller setups.
- **Local Development**: A simplified, single-tenant stack running in Docker (one DB, one set of services) to simulate the environment without the multi-tenant overhead.

---

## Component 1: Backend Services (Supabase)

### Core Services

**Database (PostgreSQL)**:
- Dedicated PostgreSQL 16+ instance per project
- Pre-installed extensions: `pgvector`, `postgis`, `timescaledb`
- Automatic daily backups and point-in-time recovery
- Connection pooling (PgBouncer)
- Web-based SQL editor and table view

**Authentication (GoTrue)**:
- Email/Password, Magic Link, OTP
- Social Providers (GitHub, Google, Apple, etc.)
- SSO (SAML 2.0) for enterprise
- Row Level Security (RLS) integration
- User management dashboard

**Object Storage (Storage API)**:
- S3-compatible API
- Resumable uploads
- Image optimization and transformation
- CDN integration
- Access policies via RLS

**Realtime**:
- WebSocket subscriptions to database changes
- Broadcast channels (pub/sub)
- Presence (user status)
- Postgres WAL replication

**Edge Functions**:
- Deno-based serverless functions
- Global distribution
- TypeScript support
- Direct database access
- Secrets injection

### DevFlow Integration

- **Project Provisioning**: Creating a DevFlow project automatically provisions all Supabase services
- **Unified Auth**: DevFlow users automatically have access to the Supabase dashboard
- **Config Management**: Service configuration managed via DevFlow Hub (IaC)

---

## Component 2: App Deployment Engine ($100k, 8 months)

### Overview

A platform-as-a-service (PaaS) layer that builds and runs application code, similar to Heroku or Dokku. It abstracts away Kubernetes/Docker complexity.

### Deployment Workflow

1. **Trigger**: `git push` to DevFlow Code or CLI command
2. **Detection**: Analyze code to detect language/framework (Node, Python, Go, etc.)
3. **Build**:
   - **Buildpacks**: Use Cloud Native Buildpacks (CNB) to create image without Dockerfile
   - **Dockerfile**: Use existing Dockerfile if present
4. **Inject**: Inject environment variables (`DATABASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`, etc.)
5. **Release**: Rolling update to Kubernetes/Docker Swarm
6. **Route**: Configure ingress/load balancer for public access

### Core Features

**Auto-Configuration**:
- Automatically injects connection strings for the project's Postgres, Redis, etc.
- Sets up `PORT` variable
- Configures health checks

**Process Management**:
- `Procfile` support for defining worker types (web, worker, clock)
- Scale replicas per process type
- Restart policies
- Resource limits (CPU/RAM)

**Domain Management**:
- Automatic `app-name.devflow.app` subdomain
- Custom domain support (`example.com`)
- Automatic Let's Encrypt SSL certificates

**Preview Environments**:
- Automatic deployment of Pull Requests
- Ephemeral URLs (`pr-123.devflow.app`)
- Database branching (copy schema/data for preview)

### Technical Stack

- **Builder**: Cloud Native Buildpacks (Pack)
- **Registry**: DevFlow Code Universal Registry
- **Orchestrator**: Kubernetes (Production) / Docker Compose (Local)
- **Ingress**: Traefik / Nginx
- **Certificate**: Cert-manager

---

## Component 3: Observability Stack ($120k, 4 months)

### Overview

Comprehensive monitoring, logging, and tracing for both the platform and user applications.

### Components

**Metrics (Prometheus + Grafana)**:
- System metrics (CPU, RAM, Disk)
- Application metrics (Request rate, Latency, Error rate)
- Database metrics (Active connections, Cache hit ratio)
- Custom metrics via StatsD/Prometheus endpoint

**Logs (Loki)**:
- Centralized logging for all services
- Structured logging (JSON) support
- Log query language (LogQL)
- Real-time log streaming (CLI & UI)

**Traces (Tempo)**:
- Distributed tracing
- OpenTelemetry support
- Visualization of request path through microservices
- Performance bottleneck identification

**Error Tracking (Sentry)**:
- Exception capturing
- Stack trace analysis
- Release tracking
- Issue management integration

### DevFlow Integration

- **Zero-Config Instrumentation**: Buildpacks automatically add OpenTelemetry agents
- **Unified Dashboard**: Metrics/Logs embedded in DevFlow UI
- **Alerting**: Rules configured in DevFlow Hub, alerts sent to Slack/Email

---

## Component 4: Platform Services ($220k, 9 months)

### Vespa Search Integration ($100k)

Unified search engine replacing separate elasticsearch/vector-db instances for advanced use cases.

- **Features**: Full-text search, vector search, hybrid search, tensor ranking
- **Use Case**: App search, knowledge base, recommendation systems
- **Integration**: Managed Vespa cluster per project

### Neo4j Graph Integration ($80k)

Managed graph database for relationship-heavy data.

- **Features**: Property graph model, Cypher query language
- **Use Case**: Social networks, recommendation engines, fraud detection
- **Integration**: Managed Neo4j instance per project

### Stripe Billing Engine ($40k)

Monetization infrastructure for user applications.

- **Features**: Subscription management, usage-based billing, invoicing
- **Integration**:
  - Sync Stripe customers with Supabase Auth users
  - Webhook handling
  - Billing portal generation

---

## API Reference

### Deployment API

```http
# List deployments
GET /api/v1/projects/{id}/deployments

# Trigger deployment
POST /api/v1/projects/{id}/deployments
{
  "ref": "main",
  "builder": "heroku/buildpacks:20"
}

# Get logs
GET /api/v1/projects/{id}/deployments/{deploy_id}/logs
```

### Infrastructure API

```http
# Get connection strings
GET /api/v1/projects/{id}/config/database
GET /api/v1/projects/{id}/config/redis

# Scale resources
PATCH /api/v1/projects/{id}/services/{service_name}
{
  "replicas": 3,
  "size": "standard-2x"
}
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Deployment Success Rate | > 99% |
| Build Time (Average) | < 2 minutes |
| API Latency (p95) | < 100ms |
| System Uptime | > 99.95% |
| Auto-config Success | 100% |

---

## Open Questions

1. **Serverless Cold Starts**: How to mitigate cold starts for Edge Functions in a self-hosted environment?
   - *Potential Solution*: Keep warm pool of workers or use Firecracker microVMs.

2. **Database Branching**: How to efficiently implement database branching for preview environments?
   - *Potential Solution*: ZFS/Btrfs snapshots or Neon-like architecture (future).

3. **Multi-Region**: Should we support multi-region deployments in the MVP?
   - *Decision*: No, single region for MVP to reduce complexity.

---

## Related PRDs

- **PRD-010**: DevFlow Code (Source of deployments)
- **PRD-012**: DevFlow Analytics (Integrated feature flags)
- **PRD-008**: Deployment Architecture (Underlying infra)

---

**Document Version**: 1.0  
**Status**: Draft  
**End of PRD-011**
