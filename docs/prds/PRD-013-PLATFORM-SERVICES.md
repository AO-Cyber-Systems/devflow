# PRD-013: Platform Services

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)  
**Investment:** $220,000 over 9 months

---

## Executive Summary

Platform Services provide advanced, specialized capabilities that power the DevFlow Runtime and Hub. These services—Vespa Search, Neo4j Graph, Stripe Billing, and the Unified SDK—abstract complex infrastructure into simple APIs for developers. They enable features like semantic search, dependency analysis, and subscription management without requiring developers to manage the underlying systems.

---

## Goals

### Primary Goals

1. **Unified Search**: Provide a single search API (Vespa) that covers code, documentation, and application data with vector + keyword support.
2. **Knowledge Graph**: Map relationships between code, tasks, docs, and people using a dedicated graph database (Neo4j).
3. **Monetization**: Enable seamless billing and subscription management for applications built on DevFlow (Stripe).
4. **Developer Experience**: Provide a single, cohesive SDK that wraps all platform capabilities.

---

## Component 1: Vespa Search Service ($100k, 4 months)

### Overview
Vespa is the world's most advanced search engine, combining vector search, full-text search, and tensor ranking. It replaces the need for separate Elasticsearch and Vector DBs for advanced use cases.

### Features
- **Hybrid Search**: Combine BM25 (keywords) with ANN (vectors) in a single query.
- **Tensor Ranking**: Use ML models to rank results based on user context.
- **Real-time Updates**: Instant indexing of high-velocity data.
- **Grouping/Aggregation**: Powerful faceted search and analytics.

### Integration
- **DevFlow Hub**: Indexes documentation and workflow data.
- **DevFlow Code**: Indexes source code and diffs.
- **DevFlow Runtime**: Available as a managed service for user apps.

### Architecture
- **Container**: `vespaengine/vespa`
- **Nodes**: Config Server + Content Nodes + Stateless Containers
- **Scaling**: Horizontal scaling of content nodes

---

## Component 2: Neo4j Graph Service ($80k, 3 months)

### Overview
Neo4j provides a property graph database to model complex relationships that relational databases struggle with.

### Use Cases
- **Code Dependency Graph**: `(Module A)-[DEPENDS_ON]->(Module B)`
- **Impact Analysis**: "If I change this function, what breaks?"
- **Social Graph**: `(User)-[FOLLOWS]->(User)`, `(User)-[CONTRIBUTED_TO]->(Repo)`
- **Knowledge Graph**: Linking documentation concepts to code implementation.

### Integration
- **Sync**: Automatic sync from Postgres (relational) to Neo4j (graph) via CDC (Change Data Capture).
- **Querying**: Cypher query endpoint exposed via API Gateway.

---

## Component 3: Stripe Billing Service ($40k, 2 months)

### Overview
A wrapper around Stripe to simplify SaaS monetization for DevFlow users.

### Features
- **Subscription Management**: Create plans (Free, Pro, Enterprise).
- **Usage-Based Billing**: Metered billing for API calls, storage, etc.
- **Customer Portal**: Self-serve portal for users to manage payments.
- **Webhooks**: Handle payment success/failure events automatically.

### Integration with Analytics
- **Feature Gating**: Link Stripe plans to DevFlow Analytics feature flags.
- **Churn Prevention**: Trigger retention workflows on failed payments.

---

## Component 4: Unified SDK ($50k, 2 months)

### Overview
A single client library for interacting with all DevFlow services.

### Design
- **Languages**: TypeScript (primary), Python, Go.
- **Module Structure**:
  ```typescript
  import { DevFlow } from '@devflow/sdk';

  const client = new DevFlow({ apiKey: '...' });

  // Search
  const results = await client.search.query('auth middleware');

  // Graph
  const deps = await client.graph.getDependencies('src/auth.ts');

  // Billing
  const subscription = await client.billing.getSubscription(userId);
  ```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Search Latency (p95) | < 50ms |
| Graph Query Latency | < 100ms |
| SDK Adoption | > 80% of projects |
| Billing Setup Time | < 15 minutes |

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Vespa Complexity** | High | Provide simplified schema templates and abstraction layer. |
| **Graph Sync Lag** | Medium | Use reliable CDC (Debezium) for eventual consistency. |
| **Stripe API Changes** | Low | Isolate Stripe calls in a versioned microservice. |

---

**End of PRD-013**
