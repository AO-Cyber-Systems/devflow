# PRD-012: DevFlow Analytics

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)  
**Investment:** $210,000 over 6 months (Month 19-24)

---

## Executive Summary

DevFlow Analytics is a comprehensive product analytics suite derived from a fork of PostHog, tightly integrated into the DevFlow ecosystem. The key differentiator is the **unification of feature flags with billing and subscription management**, enabling developers to control feature access and pricing tiers through a single interface.

**Key Innovation**: Replacing PostHog's complex ClickHouse infrastructure with a unified PostgreSQL + TimescaleDB architecture, allowing analytics data to be joined directly with application data and reducing operational complexity for self-hosting.

---

## Goals

### Primary Goals

1. **Product Analytics**: Complete event tracking, funnels, retention, and trends
2. **Feature Management**: Advanced feature flags with multivariate rollout strategies
3. **Billing Integration**: Feature flags automatically control billing tiers (e.g., "SSO" flag only enabled for "Enterprise" plan)
4. **Unified Data Model**: Single database architecture (PostgreSQL) for app and analytics
5. **Session Replay**: High-fidelity playback of user sessions for debugging

### Secondary Goals

1. A/B Testing framework
2. AI-powered churn prediction
3. Heatmaps and click tracking
4. Surveys and feedback collection
5. SQL access to analytics data

---

## Investment Breakdown

**Total**: $210,000 over 6 months

| Component | Cost | Duration | Priority |
|-----------|------|----------|----------|
| PostHog Core Fork & Migration | $80k | 3 months | P0 |
| PostgreSQL/Timescale Adapter | $60k | 3 months | P0 |
| Billing/Feature Flag Integration | $40k | 2 months | P0 |
| Session Replay Optimization | $30k | 2 months | P1 |

**Timeline**:
- Month 19-21: Fork Core + PostgreSQL Adapter
- Month 22-23: Billing Integration + Feature Flags
- Month 24: Session Replay + Polish

---

## Architecture

### Data Architecture Change

**Original PostHog**:
- **OLTP**: PostgreSQL (Metadata)
- **OLAP**: ClickHouse (Events, massive scale)
- **Complexity**: High operational burden, dual stack

**DevFlow Analytics**:
- **Unified**: PostgreSQL + TimescaleDB
- **Benefits**:
  - Simplified operations (one DB to manage)
  - JOIN capabilities (Events JOIN Users JOIN Subscriptions)
  - Lower resource footprint for self-hosting
  - Leverage existing Supabase infrastructure

### Schema Design

```sql
-- Unified Analytics Schema (TimescaleDB Hypertable)

CREATE TABLE analytics_events (
  id UUID DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id),
  event_name VARCHAR(255),
  distinct_id VARCHAR(255),
  properties JSONB,
  timestamp TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to Hypertable
SELECT create_hypertable('analytics_events', 'timestamp');

-- Feature Flags linked to Billing
CREATE TABLE feature_flags (
  id UUID PRIMARY KEY,
  key VARCHAR(255),
  description TEXT,
  billing_tiers VARCHAR[] -- ['pro', 'enterprise']
);
```

---

## Core Features

### 1. Feature Flags + Billing ($40k)

The "Killer Feature" of DevFlow Analytics. Instead of managing feature flags and billing logic separately, they are unified.

**Workflow**:
1. Create Feature Flag `sso_login`
2. Assign to Billing Tier `enterprise`
3. In code: `if (flags.enabled('sso_login')) { ... }`
4. Result: Only users on Enterprise plan pass the check. Upgrading plan automatically enables the flag.

**Capabilities**:
- **Boolean Flags**: On/Off
- **Multivariate Flags**: String/JSON values
- **Rollout Rules**: % of users, specific email domains, user properties
- **Billing Gates**: Gate features by Stripe subscription status

### 2. Product Analytics (Core)

Standard analytics capabilities ported from PostHog.

- **Trends**: Line/bar charts of events over time
- **Funnels**: Conversion steps analysis
- **Retention**: Cohort analysis
- **Paths**: User journey visualization
- **SQL Insights**: Direct SQL querying of analytics data

### 3. Session Replay ($30k)

Record and playback user interactions (DOM mutations, mouse movements, network activity).

- **Privacy**: Automatic PII masking
- **Console Logs**: Capture browser console output
- **Network**: Capture XHR/Fetch requests
- **Integration**: Link replays to Sentry errors

### 4. AI Insights

Leverage DevFlow's AI capabilities on analytics data.

- **Churn Prediction**: Analyze usage patterns to predict churn risk
- **Anomaly Detection**: Alert on unusual spikes/drops in metrics
- **Natural Language Query**: "Show me conversion rate for signups last week"

---

## Integration

### With DevFlow Code
- **Release Markers**: Deployments automatically mark charts
- **Feature Flag Code**: AI suggests feature flag implementation code

### With DevFlow Runtime
- **Zero-Config**: Analytics SDK automatically injected via buildpacks
- **Backend Events**: Server-side events captured automatically
- **Data Access**: Direct SQL access via Supabase dashboard

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **PostgreSQL Performance** | High | TimescaleDB compression, retention policies, rollup aggregations |
| **PostHog Updates** | Medium | Maintain strict adapter layer, cherry-pick upstream UI changes |
| **Data Volume** | High | Sampling options, retention limits for free tier |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Query Latency (p95) | < 200ms |
| Ingestion Rate | 10k events/sec |
| Storage Efficiency | < 100 bytes/event |

---

**End of PRD-012**
