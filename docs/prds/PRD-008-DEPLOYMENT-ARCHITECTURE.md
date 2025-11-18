# PRD-008: Deployment Architecture

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)

---

## Overview

DevFlow supports multiple deployment modes to accommodate diverse team sizes and security requirements: **Local Development** (single developer with Docker), **SaaS** (devflow.aocodex.ai for solo/small teams), **On-Premise** (Docker Compose for medium teams), and **Dedicated Cloud** (managed Kubernetes for enterprises). This PRD defines the architecture, requirements, and implementation for each deployment mode.

---

## Goals

### Primary Goals
1. **Docker-First**: Docker required for local development (PostgreSQL + Qdrant)
2. **SaaS Priority**: Build and launch SaaS platform first
3. **On-Prem Ready**: Docker Compose deployment for corporate environments
4. **Flexible Architecture**: Support local/hosted component split
5. **Corporate Firewall Support**: Work behind VPNs and strict networks

### Secondary Goals
1. Kubernetes deployment for enterprise scale (Phase 2)
2. Multi-region deployment (Phase 2)
3. High availability and disaster recovery
4. Cost optimization options
5. Easy migration between deployment modes

---

## Deployment Modes

### Mode Comparison Matrix

| Aspect | Local Dev | SaaS | On-Prem | Dedicated Cloud |
|--------|-----------|------|---------|-----------------|
| **Target Users** | Solo developer | Solo/Small teams | Medium teams | Enterprise |
| **Infrastructure** | Docker on laptop | Managed Kubernetes | Customer Docker | Managed Kubernetes |
| **Database** | Local PostgreSQL | Hosted PostgreSQL | Customer PostgreSQL | Isolated PostgreSQL |
| **Secrets** | .env file | 1Password (managed) | Customer 1Password | 1Password (managed) |
| **Cost** | Free (LLM only) | $29-99/user/month | $5K/year base | $500/month + $50/user |
| **Setup Time** | 15 minutes | 5 minutes | 2-4 hours | 1-2 days |
| **Internet Required** | Yes (for LLMs) | Yes | Optional | Yes |
| **Data Location** | Local machine | US/EU (choice) | Customer datacenter | Isolated region |
| **SLA** | N/A | 99.5% | Self-managed | 99.9% |

---

## Mode 1: Local Development

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 DEVELOPER MACHINE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Prerequisites: Docker Desktop (required)                   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Docker Stack (docker-compose up)                    │  │
│  │  ┌────────────────┐  ┌─────────────────┐            │  │
│  │  │  PostgreSQL    │  │  Qdrant         │            │  │
│  │  │  :5432         │  │  :6333          │            │  │
│  │  │  pgvector/     │  │  qdrant/        │            │  │
│  │  │  pgvector:pg16 │  │  qdrant:latest  │            │  │
│  │  └────────────────┘  └─────────────────┘            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  DevFlow Services (Node.js/Python)                   │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │  │
│  │  │ Knowledge  │  │ Workflow   │  │ MCP Gateway│    │  │
│  │  │ Hub        │  │ Engine     │  │ (stdio)    │    │  │
│  │  │ :8282      │  │ :8181      │  │ :8051      │    │  │
│  │  └────────────┘  └────────────┘  └────────────┘    │  │
│  │                                                      │  │
│  │  ┌────────────┐  ┌────────────┐                     │  │
│  │  │ Agent      │  │ Local UI   │                     │  │
│  │  │ Runtime    │  │ :3737      │                     │  │
│  │  │ (tmux/git) │  │ (React)    │                     │  │
│  │  └────────────┘  └────────────┘                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Secrets: .env file (recommended)                           │
│           1Password CLI (optional)                          │
│                                                             │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ HTTPS (to AOSentry for LLM calls)
              │
┌─────────────▼───────────────────────────────────────────────┐
│            AOSentry.aocodex.ai                              │
│            (LLM Gateway - OpenAI API Compatible)            │
└─────────────────────────────────────────────────────────────┘
```

### System Requirements

**Minimum:**
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Docker**: Docker Desktop 4.0+ or Docker Engine 20.10+
- **RAM**: 8GB (4GB for Docker containers, 4GB for system/IDE)
- **CPU**: 4 cores (2 for Docker, 2 for development)
- **Disk**: 20GB free space (10GB for Docker images/volumes, 10GB for code)
- **Network**: Stable internet for LLM calls via AOSentry

**Recommended:**
- **RAM**: 16GB or more
- **CPU**: 8 cores or more
- **Disk**: 50GB SSD
- **Network**: High-speed internet (10+ Mbps)

### Docker Setup

#### docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL with pgvector extension
  postgres:
    image: pgvector/pgvector:pg16
    container_name: devflow-postgres
    environment:
      POSTGRES_USER: devflow
      POSTGRES_PASSWORD: devflow
      POSTGRES_DB: devflow
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U devflow"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - devflow
    restart: unless-stopped

  # Qdrant vector database
  qdrant:
    image: qdrant/qdrant:latest
    container_name: devflow-qdrant
    ports:
      - "6333:6333"  # HTTP API
      - "6334:6334"  # gRPC API
    volumes:
      - qdrant-data:/qdrant/storage
    environment:
      QDRANT__SERVICE__GRPC_PORT: 6334
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:6333/health"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - devflow
    restart: unless-stopped

volumes:
  postgres-data:
    driver: local
  qdrant-data:
    driver: local

networks:
  devflow:
    driver: bridge
```

#### Quick Start Commands

```bash
# Clone repository
git clone https://github.com/aocodex/devflow.git
cd devflow

# Copy environment template
cp .env.example .env

# Edit .env with your AOSentry API key
nano .env  # or vim, code, etc.

# Start Docker containers
docker-compose up -d

# Verify containers are running
docker-compose ps
# Expected output:
# NAME                 STATUS    PORTS
# devflow-postgres     Up        0.0.0.0:5432->5432/tcp
# devflow-qdrant       Up        0.0.0.0:6333->6333/tcp

# Install dependencies
npm install  # or: pnpm install

# Run database migrations
npm run db:migrate

# Seed initial data (optional)
npm run db:seed

# Start DevFlow services
npm run dev

# In another terminal, start local UI
cd ui
npm install
npm run dev

# Access DevFlow
open http://localhost:3737
```

### Local UI (Lightweight)

Inspired by ArchonOS and Hephaestus, the local UI is a single-page application with minimal dependencies:

```
┌─────────────────────────────────────────────────────────────┐
│  DevFlow Local UI                          [Settings] [Help] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Status: ● Connected to local services                      │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Knowledge   │  │ Active      │  │ Agents      │        │
│  │ Sources     │  │ Workflows   │  │ Running     │        │
│  │    15       │  │     2       │  │     3       │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  Recent Activity                              [View All]     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ● Agent-1 started Phase 2 task                  2m   │  │
│  │ ● Crawled: docs.example.com (342 pages)         5m   │  │
│  │ ● Guardian intervened on Agent-2                8m   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Quick Actions                                              │
│  [Search Knowledge] [Create Workflow] [Monitor Agents]      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Tech Stack:**
- **Frontend**: React 18 + Vite
- **Styling**: Tailwind CSS (minimal custom CSS)
- **State**: Zustand (lightweight)
- **Real-time**: Native WebSocket API
- **Build**: Single HTML file + JS bundle (< 500KB gzipped)

**Features:**
- 🔍 Quick knowledge search
- 📊 Workflow status overview
- 👁️ Agent activity monitoring
- 📈 Real-time metrics (tasks, sources, agents)
- 🎨 Dark/light mode toggle
- 🔔 Desktop notifications (optional)

**No Authentication** - Local UI assumes single developer, no login required.

---

## Mode 2: SaaS (devflow.aocodex.ai)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 DEVELOPER MACHINE                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Claude Code  │  │  OpenCode    │                        │
│  └──────┬───────┘  └──────┬───────┘                        │
│         └─────────────────┼──────────                       │
│                           │                                 │
│                  ┌────────▼────────┐                        │
│                  │  MCP Gateway    │                        │
│                  │  (Local Client) │                        │
│                  │  Connects to    │                        │
│                  │  SaaS Backend   │                        │
│                  └────────┬────────┘                        │
│                           │                                 │
│                  ┌────────▼────────┐                        │
│                  │  Agent Runtime  │                        │
│                  │  (tmux/git)     │                        │
│                  │  Local only     │                        │
│                  └─────────────────┘                        │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ HTTPS + WebSocket
              │ (authenticated with DEVFLOW_API_KEY)
              │
┌─────────────▼───────────────────────────────────────────────┐
│          devflow.aocodex.ai (SaaS Platform)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Global Load Balancer (CloudFlare)                          │
│  ├── US Region (Primary)                                    │
│  └── EU Region (GDPR compliance)                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     Kubernetes Cluster (EKS/GKE)                    │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │   │
│  │  │ Knowledge    │  │ Workflow     │  │ MCP      │ │   │
│  │  │ Hub API      │  │ Engine API   │  │ Gateway  │ │   │
│  │  │ (3 replicas) │  │ (5 replicas) │  │ (3 rep)  │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │   │
│  │  │ Integration  │  │ API Gateway  │  │ Web      │ │   │
│  │  │ Services     │  │ (Rate Limit) │  │ Dashboard│ │   │
│  │  │ (2 replicas) │  │              │  │ (CDN)    │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Managed Databases                                  │   │
│  │  ┌──────────────────┐  ┌──────────────────┐        │   │
│  │  │ PostgreSQL       │  │ Qdrant Cloud     │        │   │
│  │  │ (RDS Multi-AZ)   │  │ (Managed)        │        │   │
│  │  │ Read replicas: 2 │  │ Sharded clusters │        │   │
│  │  └──────────────────┘  └──────────────────┘        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Secrets Management                                 │   │
│  │  1Password Connect (Managed by AOCodex)             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ All LLM Calls
              │
┌─────────────▼───────────────────────────────────────────────┐
│            AOSentry.aocodex.ai                              │
└─────────────────────────────────────────────────────────────┘
```

### SaaS Features

**Included in All Plans:**
- ✅ Managed infrastructure (no Docker required)
- ✅ Automatic backups (daily, 30-day retention)
- ✅ SSL certificates (automatic renewal)
- ✅ 99.5% uptime SLA
- ✅ Email support (24-hour response)
- ✅ Automatic updates (security patches)
- ✅ Web dashboard (full-featured)

**Pricing Tiers:**

```yaml
Free Tier:
  price: $0/month
  limits:
    users: 1
    knowledge_sources: 10
    workflows_per_month: 5
    storage: 1GB
    llm_calls_per_month: 1000
  features:
    - Basic knowledge management
    - Simple workflows (3 phases max)
    - Community support

Pro Tier:
  price: $29/user/month
  limits:
    users: 1-5
    knowledge_sources: unlimited
    workflows_per_month: unlimited
    storage: 50GB
    llm_calls_per_month: 50000
  features:
    - Advanced workflows (unlimited phases)
    - Priority support (12-hour response)
    - Integration with Jira/GitHub
    - Custom MCP tools
    - API access

Team Tier:
  price: $99/month base + $25/user/month
  limits:
    users: 5-50
    knowledge_sources: unlimited
    workflows_per_month: unlimited
    storage: 500GB
    llm_calls_per_month: 250000
  features:
    - Shared knowledge base
    - Team collaboration
    - Admin controls (RBAC)
    - SSO integration (SAML)
    - Priority support (4-hour response)
    - Dedicated account manager

Enterprise Tier:
  price: Custom (starts at $500/month)
  limits:
    users: unlimited
    everything: unlimited
  features:
    - Dedicated cloud (isolated tenant)
    - Custom domain (devflow.yourcompany.com)
    - 99.9% SLA
    - 24/7 phone support
    - On-premise option available
    - Custom integrations
    - Professional services
```

### Multi-Tenancy Isolation

```sql
-- Database-level isolation

CREATE SCHEMA tenant_abc123;
CREATE SCHEMA tenant_def456;

-- Each tenant gets:
-- 1. Isolated schema in shared PostgreSQL
-- 2. Dedicated Qdrant collection
-- 3. Separate rate limits
-- 4. Isolated secrets in 1Password vault

-- Row-Level Security (RLS) for shared tables
CREATE POLICY tenant_isolation ON users
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

### Monitoring & SLA

**Monitoring Stack:**
- **Metrics**: Prometheus + Grafana
- **Logs**: Loki + Grafana
- **Traces**: Tempo + Grafana
- **Alerts**: PagerDuty
- **Status Page**: status.devflow.aocodex.ai

**SLA Guarantees:**

| Tier | Uptime SLA | Response Time (p95) | Support Response |
|------|------------|---------------------|------------------|
| Free | 95% | < 2s | Community |
| Pro | 99.5% | < 1s | 12 hours |
| Team | 99.5% | < 500ms | 4 hours |
| Enterprise | 99.9% | < 200ms | 1 hour |

---

## Mode 3: On-Premise (Docker Compose)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│          CORPORATE NETWORK (VPN/Firewall)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  devflow.company.internal (or devflow.local)                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Docker Compose Stack (Single Server)               │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │   │
│  │  │ PostgreSQL   │  │ Qdrant       │  │ 1Password│ │   │
│  │  │ + pgvector   │  │              │  │ Connect  │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │   │
│  │  │ Knowledge    │  │ Workflow     │  │ MCP      │ │   │
│  │  │ Hub          │  │ Engine       │  │ Gateway  │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │ Integration  │  │ Web          │               │   │
│  │  │ Services     │  │ Dashboard    │               │   │
│  │  └──────────────┘  └──────────────┘               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Developers connect from workstations via corporate VPN     │
│                                                             │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ HTTPS (outbound only, for LLM calls)
              │ Optional: Can route to on-prem LLMs via AOSentry
              │
┌─────────────▼───────────────────────────────────────────────┐
│            AOSentry.aocodex.ai                              │
│            (or on-prem LLMs via AOSentry routing)           │
└─────────────────────────────────────────────────────────────┘
```

### Docker Compose Configuration

```yaml
# docker-compose.onprem.yml

version: '3.8'

services:
  # PostgreSQL with pgvector
  postgres:
    image: pgvector/pgvector:pg16
    container_name: devflow-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-devflow}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-devflow}
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-devflow}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - devflow-internal
    restart: always
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G

  # Qdrant vector database
  qdrant:
    image: qdrant/qdrant:latest
    container_name: devflow-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant-data:/qdrant/storage
      - ./qdrant-snapshots:/qdrant/snapshots
    environment:
      QDRANT__SERVICE__GRPC_PORT: 6334
      QDRANT__SERVICE__HTTP_PORT: 6333
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:6333/health"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - devflow-internal
    restart: always
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '2'
          memory: 2G

  # 1Password Connect (optional but recommended)
  onepassword-connect:
    image: 1password/connect-api:latest
    container_name: devflow-1password
    ports:
      - "8080:8080"
    volumes:
      - ./secrets/1password-credentials.json:/home/opuser/.op/1password-credentials.json:ro
      - onepassword-data:/home/opuser/.op/data
    environment:
      OP_SESSION: ${OP_SESSION}
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - devflow-internal
    restart: always

  # Knowledge Hub Service
  knowledge-hub:
    image: devflow/knowledge-hub:${DEVFLOW_VERSION:-latest}
    container_name: devflow-knowledge-hub
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-devflow}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-devflow}
      QDRANT_URL: http://qdrant:6333
      AOSENTRY_API_KEY: ${AOSENTRY_API_KEY}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    ports:
      - "8282:8282"
    volumes:
      - knowledge-uploads:/app/uploads
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:8282/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - devflow-internal
    restart: always

  # Workflow Engine Service
  workflow-engine:
    image: devflow/workflow-engine:${DEVFLOW_VERSION:-latest}
    container_name: devflow-workflow-engine
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-devflow}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-devflow}
      AOSENTRY_API_KEY: ${AOSENTRY_API_KEY}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    ports:
      - "8181:8181"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # For spawning agent containers
      - agent-worktrees:/worktrees
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:8181/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - devflow-internal
    restart: always

  # MCP Gateway Service
  mcp-gateway:
    image: devflow/mcp-gateway:${DEVFLOW_VERSION:-latest}
    container_name: devflow-mcp-gateway
    depends_on:
      - knowledge-hub
      - workflow-engine
    environment:
      KNOWLEDGE_HUB_URL: http://knowledge-hub:8282
      WORKFLOW_ENGINE_URL: http://workflow-engine:8181
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    ports:
      - "8051:8051"
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:8051/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - devflow-internal
    restart: always

  # Integration Services
  integration-services:
    image: devflow/integration-services:${DEVFLOW_VERSION:-latest}
    container_name: devflow-integrations
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-devflow}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-devflow}
      ATLASSIAN_CLIENT_ID: ${ATLASSIAN_CLIENT_ID}
      ATLASSIAN_CLIENT_SECRET: ${ATLASSIAN_CLIENT_SECRET}
      GITHUB_CLIENT_ID: ${GITHUB_CLIENT_ID}
      GITHUB_CLIENT_SECRET: ${GITHUB_CLIENT_SECRET}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    ports:
      - "8383:8383"
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:8383/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - devflow-internal
    restart: always

  # Web Dashboard
  web-dashboard:
    image: devflow/web-dashboard:${DEVFLOW_VERSION:-latest}
    container_name: devflow-web-dashboard
    environment:
      VITE_API_BASE_URL: http://nginx:80/api
      VITE_WS_URL: ws://nginx:80/ws
    networks:
      - devflow-internal
    restart: always

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: devflow-nginx
    depends_on:
      - knowledge-hub
      - workflow-engine
      - mcp-gateway
      - integration-services
      - web-dashboard
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:80/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - devflow-internal
    restart: always

volumes:
  postgres-data:
    driver: local
  qdrant-data:
    driver: local
  onepassword-data:
    driver: local
  knowledge-uploads:
    driver: local
  agent-worktrees:
    driver: local

networks:
  devflow-internal:
    driver: bridge
```

### Installation Guide

```bash
# On-Premise Installation Guide

# Step 1: Prepare Server
# - Ubuntu 22.04 LTS (recommended)
# - Docker 24.0+ and Docker Compose 2.20+
# - 8 CPU cores, 32GB RAM, 500GB SSD minimum

# Step 2: Clone DevFlow
git clone https://github.com/aocodex/devflow.git
cd devflow/deploy/onprem

# Step 3: Configure Environment
cp .env.example .env.production
nano .env.production

# Required variables:
# - POSTGRES_PASSWORD (generate with: openssl rand -base64 32)
# - AOSENTRY_API_KEY (from AOSentry dashboard)
# - SECRET_ENCRYPTION_KEY (generate with: openssl rand -base64 32)

# Step 4: Configure 1Password (Recommended)
# - Create service account in 1Password
# - Download credentials JSON
# - Place in ./secrets/1password-credentials.json

# Step 5: Generate SSL Certificates
# Option A: Let's Encrypt (if public domain)
certbot certonly --standalone -d devflow.company.com

# Option B: Self-signed (internal network)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./ssl/devflow.key \
  -out ./ssl/devflow.crt

# Step 6: Start DevFlow
docker-compose -f docker-compose.onprem.yml up -d

# Step 7: Verify Services
docker-compose -f docker-compose.onprem.yml ps
# All services should show "Up" status

# Step 8: Run Database Migrations
docker-compose -f docker-compose.onprem.yml exec knowledge-hub npm run db:migrate

# Step 9: Create Admin User
docker-compose -f docker-compose.onprem.yml exec knowledge-hub npm run create-admin

# Step 10: Access DevFlow
open https://devflow.company.internal
```

### Backup & Recovery

```bash
# Automated Backup Script (backup.sh)

#!/bin/bash

BACKUP_DIR="/backups/devflow"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker-compose -f docker-compose.onprem.yml exec -T postgres \
  pg_dump -U devflow devflow | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Backup Qdrant
docker-compose -f docker-compose.onprem.yml exec -T qdrant \
  wget -O- http://localhost:6333/collections/devflow_knowledge/snapshots | \
  gzip > "$BACKUP_DIR/qdrant_$DATE.snapshot.gz"

# Backup uploads
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" /var/lib/docker/volumes/devflow_knowledge-uploads

# Retain last 30 days
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

---

## Network Architecture

### Firewall Configuration

**Inbound Rules (Required):**
```
Port 443 (HTTPS) - Web dashboard access
Port 80 (HTTP) - Redirect to HTTPS
```

**Outbound Rules (Required):**
```
Port 443 (HTTPS) - To aosentry.aocodex.ai (LLM calls)
Port 443 (HTTPS) - To atlassian.net (if using Jira/Confluence)
Port 443 (HTTPS) - To github.com (if using GitHub integration)
```

**Internal Ports (Container-to-Container):**
```
5432 - PostgreSQL
6333 - Qdrant HTTP
6334 - Qdrant gRPC
8080 - 1Password Connect
8181 - Workflow Engine
8282 - Knowledge Hub
8051 - MCP Gateway
8383 - Integration Services
```

### VPN Integration

DevFlow supports connection through corporate VPNs:

```yaml
# docker-compose.onprem.yml additions for VPN

services:
  # ... other services ...

  vpn-client:
    image: dperson/openvpn-client
    container_name: devflow-vpn
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun
    volumes:
      - ./vpn-config:/vpn:ro
    environment:
      VPN_CONFIG: /vpn/company.ovpn
      VPN_USER: ${VPN_USER}
      VPN_PASS: ${VPN_PASS}
    networks:
      - devflow-internal
    restart: always

  # Route outbound LLM calls through VPN
  knowledge-hub:
    # ... existing config ...
    network_mode: "service:vpn-client"
    depends_on:
      - vpn-client
```

---

## Migration Paths

### Local → SaaS

```bash
# Export local data
npm run export-data --output=devflow-export.json

# Upload to SaaS
# 1. Create account at devflow.aocodex.ai
# 2. Navigate to Settings → Import
# 3. Upload devflow-export.json
# 4. Verify data imported successfully

# Update local .env to use SaaS
DEVFLOW_MODE=saas
DEVFLOW_API_KEY=<your-saas-api-key>

# Stop local services
docker-compose down

# Remove local data (optional)
docker volume rm devflow_postgres-data devflow_qdrant-data
```

### SaaS → On-Premise

```bash
# 1. Export from SaaS
# Login to devflow.aocodex.ai
# Settings → Export → Download full export

# 2. Setup on-premise deployment
# Follow on-premise installation guide

# 3. Import data
docker-compose -f docker-compose.onprem.yml exec knowledge-hub \
  npm run import-data -- --input=/imports/devflow-export.json

# 4. Update team to use on-premise
# Distribute new .env to team members:
DEVFLOW_MODE=onprem
DEVFLOW_API_URL=https://devflow.company.internal
```

---

## Success Metrics

### Deployment Success

| Metric | Local Dev | SaaS | On-Prem |
|--------|-----------|------|---------|
| Setup time | < 15 min | < 5 min | < 4 hours |
| First successful query | < 30 min | < 10 min | < 6 hours |
| Team onboarding | < 1 day | < 1 hour | < 1 week |

### Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| API response time (p95) | < 500ms | Yes |
| Knowledge search (p95) | < 2s | Yes |
| Docker startup time | < 60s | No |
| Database migration time | < 5 min | No |

---

## Future Enhancements

### Phase 1 (Q2 2026)
1. **Kubernetes Deployment** - Helm charts for enterprise scale
2. **Multi-region SaaS** - US, EU, APAC regions
3. **Air-gapped Installation** - Fully offline on-prem deployment
4. **ARM Support** - Apple Silicon and ARM servers

### Phase 2 (Q3 2026)
1. **High Availability** - Multi-node PostgreSQL cluster
2. **Auto-scaling** - Kubernetes HPA for services
3. **Disaster Recovery** - Automated failover and backups
4. **Observability Platform** - Grafana stack deployment

---

**End of PRD-008**
