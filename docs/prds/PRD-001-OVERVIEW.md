# PRD-001: DevFlow System Overview

**Version:** 2.0  
**Status:** Active Development  
**Last Updated:** November 18, 2025  
**Author:** DevFlow Team

---

## Executive Summary

DevFlow is a **complete AI-native development platform** that combines AI orchestration, source control, CI/CD, and backend services into one integrated system. DevFlow synthesizes the knowledge management capabilities of Archon with the adaptive workflow execution of Hephaestus, while adding comprehensive Git hosting, package management, and backend infrastructure.

**Platform Investment**: $2.22M over 24 months

**Three Integrated Products**:
1. **DevFlow Hub** - AI Orchestration & Knowledge Management ($220k, 12 months)
2. **DevFlow Code** - Git Hosting, CI/CD, Universal Package Registry ($540k, 18 months)
3. **DevFlow Runtime** - Complete Backend Platform ($1.36M, 24 months)

DevFlow is the **only self-hosted platform** combining AI development tools, source control, and backend services with true data sovereignty.

---

## Vision

**DevFlow creates the complete development platform where:**

- AI agents have comprehensive project knowledge and adapt workflows dynamically
- Source code, artifacts, and packages are managed in a universal registry
- Backend services (database, auth, storage, functions) are integrated out-of-box
- Feature flags, analytics, and observability drive data-informed decisions
- Everything works locally or in the cloud with seamless migration between modes

---

## Problem Statement

Current development platforms force you to cobble together multiple tools:

1. **Fragmented Development Tools**:
   - GitHub for code → CircleCI for CI/CD → Heroku for hosting → PostHog for analytics
   - Each tool requires separate billing, authentication, and integration
   - No unified experience or data sharing across tools

2. **Limited AI Integration**:
   - AI coding assistants lack access to comprehensive project knowledge
   - No orchestration for multi-agent workflows
   - Rigid automation that breaks when reality diverges from predictions

3. **Vendor Lock-in**:
   - Cloud-only solutions prevent self-hosting for compliance
   - No data sovereignty for regulated industries
   - Migration between providers is painful and risky

4. **Incomplete Platforms**:
   - GitHub: Great for code, but limited backend services
   - Supabase: Great for backend, but no Git hosting or CI/CD
   - Neither has AI orchestration or knowledge management

---

## Solution: Three-Product Platform

DevFlow addresses these challenges with three integrated products that work seamlessly together:

### 1. **DevFlow Hub** ($220k, 12 months) - AI Orchestration
**Inspired by Archon + Hephaestus**

- **Knowledge Management**: Web crawling, document processing, vector search
- **Adaptive Workflows**: Semi-structured phases, dynamic task creation
- **MCP Gateway**: Standardized AI agent tool access
- **Guardian Monitoring**: Keep agents aligned with goals
- **SDLC Integrations**: Jira, Confluence, GitHub bidirectional sync

**Key Innovation**: Workflows that adapt based on discoveries, not rigid pre-planned scripts

### 2. **DevFlow Code** ($540k, 18 months) - Source Control & CI/CD
**GitHub Alternative with AI Enhancements**

- **Git Server**: Gitea-based fork with AI-powered code review
- **CI/CD**: GitHub Actions-compatible pipeline system
- **Universal Package Registry**: npm, pip, Docker, apt, cargo, maven, etc.
- **Project Management**: Issues, pull requests, project boards
- **Security Scanning**: Vulnerability detection, dependency audits

**Key Innovation**: Universal package registry supporting ALL package managers in one place

### 3. **DevFlow Runtime** ($1.36M, 24 months) - Complete Backend
**Supabase + Deployment + Analytics**

- **Supabase Foundation**: PostgreSQL, Auth, Storage, Realtime, Edge Functions
- **App Deployment**: git push deploy with automatic buildpacks
- **Observability**: Prometheus, Loki, Tempo, Sentry integration
- **DevFlow Analytics**: PostHog fork with feature flags + billing integration
- **Search & Graph**: Vespa full-text/vector search, Neo4j knowledge graph
- **Billing**: Stripe integration for subscriptions

**Key Innovation**: Feature flags that control billing tiers, enabling sophisticated pricing

---

## Why Three Products?

### Better Together, Useful Apart

**Use DevFlow Hub Alone**:
- AI orchestration with existing Git (GitHub, GitLab)
- Knowledge management for any project
- Adaptive workflows with external CI/CD

**Use DevFlow Code Alone**:
- Self-hosted Git alternative to GitHub
- Universal package registry for all artifacts
- CI/CD without AI orchestration

**Use DevFlow Runtime Alone**:
- Backend platform like Supabase
- App deployment like Heroku
- Analytics without Git hosting

**Use All Three Together**:
- Complete integrated platform
- Automatic configuration (DATABASE_URL, etc.)
- Unified billing and authentication
- Data sovereignty with self-hosting option

---

## Core Principles

1. **Structure Where It Matters**: Define work types, phase goals, and completion criteria, but let agents fill in the details

2. **Flexibility Where You Need It**: Allow agents to create new tasks based on discoveries without pre-planning every scenario

3. **Knowledge-Driven Execution**: Every agent has access to the full project knowledge base to make informed decisions

4. **Observable by Default**: Comprehensive visibility into what agents are doing, discovering, and deciding

5. **Microservices Architecture**: Independent, scalable services with clear responsibilities and HTTP-based communication

---

## Complete Platform Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DevFlow Platform                               │
│                         ($2.22M over 24 months)                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────────┐
│  DevFlow Hub    │      │  DevFlow Code   │      │  DevFlow Runtime    │
│  ($220k/12mo)   │      │  ($540k/18mo)   │      │  ($1.36M/24mo)      │
├─────────────────┤      ├─────────────────┤      ├─────────────────────┤
│ Knowledge Hub   │      │ Git Server      │      │ Supabase (DB/Auth)  │
│ Workflow Engine │      │ Pull Requests   │      │ App Deployment      │
│ MCP Gateway     │      │ CI/CD Pipelines │      │ Observability       │
│ Agent Runtime   │      │ Package Registry│      │ Analytics (PostHog) │
│ Guardian System │      │ Security Scan   │      │ Search (Vespa)      │
│ UI Dashboard    │      │ Project Mgmt    │      │ Graph (Neo4j)       │
│ Integrations    │      │ AI Code Review  │      │ Billing (Stripe)    │
└─────────────────┘      └─────────────────┘      └─────────────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                         ┌──────────────────┐
                         │  Cross-Cutting   │
                         │    Services      │
                         ├──────────────────┤
                         │ Secrets (1Pass)  │
                         │ AOSentry (LLM)   │
                         │ Docker/K8s       │
                         │ PostgreSQL       │
                         └──────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌──────────┐    ┌──────────┐    ┌──────────┐
            │ DevFlow  │    │ DevFlow  │    │   Web    │
            │   CLI    │    │ Desktop  │    │    UI    │
            │          │    │ (Electron)│   │          │
            └──────────┘    └──────────┘    └──────────┘
```

### Product Integration Points

**Hub ↔ Code**:
- Workflows trigger CI/CD pipelines
- AI agents create pull requests
- Code review results update knowledge base
- Package dependencies inform workflow decisions

**Code ↔ Runtime**:
- git push triggers app deployment
- CI/CD publishes packages to registry
- Runtime services available as package dependencies
- Observability integrated with build logs

**Hub ↔ Runtime**:
- Knowledge base searches application data
- Workflows deploy to Runtime infrastructure
- Feature flags (Analytics) control workflow rollout
- Agent usage tracked in Analytics

**All Three**:
- Single authentication (Supabase Auth)
- Unified billing (Stripe via Runtime)
- Shared PostgreSQL database
- Consistent UI/UX across products

---

## Key Features

### Phase 1: Foundation (MVP)

1. **Knowledge Management**
   - Web crawling with sitemap detection
   - PDF/document upload and processing
   - Vector search with embeddings
   - Source organization and tagging

2. **Workflow Orchestration**
   - Phase-based workflow definition
   - Dynamic task creation by agents
   - Kanban board coordination
   - Basic Guardian monitoring

3. **MCP Integration**
   - Knowledge access tools
   - Task management tools
   - Memory storage tools
   - Agent coordination tools

4. **UI Dashboard**
   - Knowledge base browser
   - Workflow status view
   - Task list and Kanban
   - Basic configuration

### Phase 2: Enhancement

1. **Advanced RAG**
   - Hybrid search strategies
   - Contextual embeddings
   - Result reranking
   - Code example extraction

2. **Enhanced Workflows**
   - Multi-agent coordination patterns
   - Workflow templates
   - Conflict resolution strategies
   - Advanced Guardian interventions

3. **Observability**
   - Real-time agent trajectory monitoring
   - Decision tree visualization
   - Performance analytics
   - Cost tracking

4. **SDLC Tool Integrations** (See PRD-006)
   - **Atlassian Integration** (Jira, Confluence, Bitbucket)
   - **GitHub Integration** (Issues, PRs, Projects)
   - Bidirectional sync with hierarchy enforcement
   - User-level OAuth authentication
   - Conflict resolution dashboard

### Phase 3: Enterprise

1. **Multi-tenancy**
   - Team workspaces
   - Access controls
   - Resource quotas
   - Audit logging

2. **Scalability**
   - Horizontal service scaling
   - Distributed task queue
   - Caching layer
   - Load balancing

3. **Security**
   - SSO integration
   - Role-based access control
   - API key management
   - Encryption at rest

4. **Analytics**
   - Workflow success metrics
   - Agent performance analysis
   - Cost optimization insights
   - Team productivity tracking

---

## Success Metrics

### User Success
- Time to first successful workflow: < 30 minutes
- Knowledge retrieval accuracy: > 90%
- Agent task completion rate: > 85%
- User satisfaction (NPS): > 50

### Technical Performance
- Knowledge query latency: < 200ms (p95)
- Workflow coordination latency: < 500ms
- System uptime: > 99.5%
- Agent spawn time: < 5 seconds

### Business Impact
- Reduction in manual coding time: > 40%
- Increase in code quality (fewer bugs): > 30%
- Developer productivity gain: > 2x
- Knowledge reuse rate: > 70%

---

## Technology Stack

### Backend Services
- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase) + PGVector
- **Vector Store**: Qdrant
- **Task Queue**: Redis + Celery
- **Real-time**: Socket.IO / SSE

### Frontend
- **Framework**: React + TypeScript
- **Build**: Vite
- **Styling**: TailwindCSS
- **State**: Zustand / React Query
- **Visualization**: D3.js / Mermaid

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose (dev), Kubernetes (prod)
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack
- **Tracing**: OpenTelemetry

### AI/ML
- **LLM Providers**: OpenAI, Anthropic, OpenRouter
- **Embeddings**: OpenAI text-embedding-3-large
- **Agent Runtime**: Claude Code, OpenCode
- **Protocol**: Model Context Protocol (MCP)

---

## Platform Investment Summary

### Development Costs by Product

**DevFlow Hub** ($220k, 12 months):
- Knowledge Hub: $80k (4 months)
- Workflow Engine: $60k (3 months)
- MCP Gateway: $40k (2 months)
- UI Dashboard: $40k (3 months)

**DevFlow Code** ($540k, 18 months):
- Git Server (Gitea fork): $100k (6 months)
- CI/CD System: $80k (4 months)
- AI Code Review: $120k (4 months)
- Universal Package Registry: $140k (6 months)
- Project Management: $60k (3 months)
- Integration: $40k (2 months)

**DevFlow Runtime** ($1.36M, 24 months):
- Supabase Base: $450k (15 months)
- App Deployment: $100k (8 months)
- Observability Stack: $120k (4 months)
- DevFlow Analytics (PostHog fork): $210k (6 months)
- Vespa Search: $100k (4 months)
- Neo4j Graph: $80k (3 months)
- Stripe Integration: $40k (2 months)
- SDK Integration: $50k (2 months)

**Optional**:
- DevFlow CLI: Included in each product
- DevFlow Desktop: $100k (6 months)

**Total**: $2.22M over 24 months (excluding Desktop)

### Timeline Milestones

```
Month 1:    DevFlow Hub + Runtime start
Month 3:    DevFlow Code starts
Month 12:   DevFlow Hub MVP complete
Month 15:   Supabase foundation complete
Month 18:   DevFlow Code complete
Month 19:   DevFlow Analytics (PostHog fork) starts
Month 24:   Complete platform launch
```

---

## Competitive Positioning

### DevFlow vs Existing Solutions

| Feature | GitHub+Actions | Supabase | GitLab | DevFlow |
|---------|----------------|----------|--------|---------|
| **Git Hosting** | ✅ | ❌ | ✅ | ✅ |
| **CI/CD** | ✅ | ❌ | ✅ | ✅ |
| **Package Registry** | Limited | ❌ | Limited | Universal |
| **Backend (DB/Auth)** | ❌ | ✅ | ❌ | ✅ |
| **App Deployment** | ❌ | ✅ Functions | ❌ | ✅ Containers |
| **AI Orchestration** | ❌ | ❌ | ❌ | ✅ |
| **Knowledge Management** | ❌ | ❌ | ❌ | ✅ |
| **Analytics** | Limited | Limited | Limited | ✅ PostHog |
| **Self-Hosted** | ❌ | ✅ | ✅ | ✅ |
| **Feature Flags** | ❌ | ❌ | ❌ | ✅ w/ Billing |
| **Unified Platform** | ❌ | Partial | Partial | ✅ |

### Unique Value Propositions

1. **Only Platform with AI Orchestration + Git + Backend** - Complete development lifecycle in one system
2. **Universal Package Registry** - npm, pip, Docker, apt, all in one place
3. **Feature Flags + Billing Integration** - Sophisticated pricing and gradual rollouts
4. **True Data Sovereignty** - Complete self-hosting with cloud option
5. **Integrated Knowledge Management** - AI agents with full project context

### Target Markets

**Startups** ($99-499/month):
- Complete platform from day 1
- Scales as they grow
- No vendor juggling

**Enterprises** (Self-hosted):
- Compliance and data sovereignty
- On-premise or air-gapped
- Custom SLAs

**Dev Tools Companies**:
- Platform to build on top of
- White-label options
- API-first architecture

---

## Non-Goals (Out of Scope)

1. **Code Editor Replacement**: DevFlow is not replacing VS Code, Cursor, or Windsurf
2. **Direct Code Execution**: Agents work through CLI tools, not direct Python exec
3. **General Purpose Cloud**: Not competing with AWS/GCP/Azure infrastructure
4. **General Purpose Chatbot**: Focused on development workflows, not ChatGPT replacement
5. **Mobile Development**: No native mobile app platform (web apps via Runtime only)

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM API costs too high | High | Medium | Implement caching, rate limiting, model selection strategies |
| Agent coordination failures | High | Medium | Robust Guardian system, conflict resolution, rollback mechanisms |
| Knowledge base accuracy issues | Medium | Medium | Human-in-the-loop validation, quality scoring, source verification |
| Scaling challenges | High | Low | Microservices architecture, horizontal scaling design from start |
| Security vulnerabilities | High | Low | Regular security audits, sandboxed agent execution, access controls |
| User adoption barriers | Medium | Medium | Comprehensive documentation, example workflows, onboarding flow |

---

## Development Roadmap

### Phase 1: DevFlow Hub Foundation (Months 1-12)
**Investment**: $220k

**Deliverables**:
- Knowledge Hub with web crawling, document processing, RAG
- Workflow Engine with semi-structured phases and Kanban coordination
- MCP Gateway for AI agent tool access
- UI Dashboard for monitoring and control
- Integrations with Jira/Confluence/GitHub
- Secrets management (1Password + .env)
- AOSentry LLM gateway integration

**Success Metrics**:
- Can ingest and search documentation (>90% accuracy)
- Can run end-to-end workflow (PRD → Code)
- Agents coordinate via Kanban (no duplicate work)
- Guardian prevents workflow drift (>90% intervention success)

### Phase 2: DevFlow Code (Months 3-18)
**Investment**: $540k (parallel with Hub)

**Deliverables**:
- Self-hosted Git server (Gitea fork with AI enhancements)
- Pull/merge request system with AI code review
- GitHub Actions-compatible CI/CD
- Universal Package Registry (npm, pip, Docker, apt, cargo, etc.)
- Project management (issues, boards)
- Security scanning and vulnerability detection

**Success Metrics**:
- Can host Git repositories and handle PRs
- CI/CD pipelines execute reliably (>95% success rate)
- Package registry supports 10+ package managers
- AI code review provides actionable feedback (>80% helpful)

### Phase 3: DevFlow Runtime Core (Months 1-18)
**Investment**: $670k (parallel with Hub + Code)

**Deliverables**:
- Supabase foundation (PostgreSQL, Auth, Storage, Realtime, Functions)
- Application deployment (git push deploy with buildpacks)
- Background workers and scheduled jobs
- Observability stack (Prometheus, Loki, Tempo, Sentry)
- Vespa Search (full-text + vector + hybrid)
- Neo4j Knowledge Graph (code dependencies)
- Stripe Integration (billing)
- Unified SDK

**Success Metrics**:
- Can deploy apps with single command
- Database, auth, storage work out-of-box
- Monitoring and logging provide visibility
- Search and graph enhance platform value

### Phase 4: DevFlow Analytics (Months 19-24)
**Investment**: $210k (after Hub/Code stable)

**Deliverables**:
- PostHog fork with PostgreSQL + TimescaleDB backend
- Feature flags integrated with billing/subscriptions
- A/B testing framework for product decisions
- Session replay for debugging
- Funnel analysis and conversion tracking
- AI-powered churn prediction

**Success Metrics**:
- Feature flags control billing tiers (>5 tiers)
- A/B tests inform product decisions (>10 experiments)
- Session replay helps debug issues (>50% faster resolution)
- Churn prediction enables retention (>20% improvement)

### Phase 5: Polish & Launch (Month 24+)
**Investment**: Ongoing

**Deliverables**:
- DevFlow CLI unified tool
- DevFlow Desktop (Electron app, optional)
- Documentation and tutorials
- Community templates
- Plugin system
- Mobile companion (future)

---

## Open Questions

### Product Strategy

1. **Launch Strategy**: Launch all three products simultaneously (Month 24) or phase them?
   - Option A: Hub (Month 12) → Code (Month 18) → Runtime (Month 24)
   - Option B: Integrated beta (Month 18) → Full launch (Month 24)

2. **Open Source Model**: Which components should be open source?
   - Option A: All open source, commercial hosting/support
   - Option B: Hub open source, Code/Runtime commercial
   - Option C: Core open source, enterprise features commercial

3. **Pricing Tiers**: How many tiers and what features in each?
   - Suggested: Free (solo), Pro ($99/mo), Team ($499/mo), Enterprise (custom)

### Technical Decisions

4. **Gitea Fork vs Custom**: Should we fork Gitea or build Git server from scratch?
   - Recommendation: Fork Gitea (faster, proven, community)

5. **Analytics Backend**: PostgreSQL + TimescaleDB vs ClickHouse for PostHog?
   - Recommendation: PostgreSQL + TimescaleDB (unified data model)

6. **Kubernetes Requirement**: Support Docker Compose only or require Kubernetes?
   - Recommendation: Docker Compose (dev/small), Kubernetes (prod/scale)

### Go-to-Market

7. **Target Launch Date**: When should SaaS go live?
   - Suggestion: Month 12 (Hub only), Month 18 (+ Code), Month 24 (complete)

8. **Revenue Projections**: Expected revenue at 12/24/36 months?
   - Needs: Financial model with customer acquisition assumptions

9. **Fundraising Strategy**: Bootstrap, seed round, or Series A?
   - Consideration: $2.22M development cost + operations + marketing

---

## Related PRDs

### Core Platform
- [PRD-007: Secrets & Environment Management](./PRD-007-SECRETS-MANAGEMENT.md)
- [PRD-008: Deployment Architecture](./PRD-008-DEPLOYMENT-ARCHITECTURE.md)
- [PRD-009: AOSentry Integration](./PRD-009-AOSENTRY-INTEGRATION.md)

### DevFlow Hub (AI Orchestration)
- [PRD-002: Knowledge Hub Service](./PRD-002-KNOWLEDGE-HUB.md)
- [PRD-003: Adaptive Workflow Engine](./PRD-003-WORKFLOW-ENGINE.md)
- [PRD-004: MCP Gateway Service](./PRD-004-MCP-GATEWAY.md)
- [PRD-005: Unified UI Dashboard](./PRD-005-UI-DASHBOARD.md)
- [PRD-006: SDLC Tool Integrations](./PRD-006-INTEGRATIONS.md)

### DevFlow Code (Git + CI/CD)
- PRD-010: DevFlow Code *(to be created)*

### DevFlow Runtime (Backend Platform)
- PRD-011: DevFlow Runtime *(to be created)*
- PRD-012: DevFlow Analytics *(to be created)*
- PRD-013: Additional Platform Services *(to be created)*

### Developer Tools
- PRD-014: DevFlow CLI *(to be created)*
- PRD-015: DevFlow Desktop *(to be created)*

### Planning Documents
- [PRD Index (README)](./README.md)
- [PRD Update Plan](../PRD_UPDATE_PLAN.md)
- [Implementation Summary](../IMPLEMENTATION_SUMMARY.md)
- [Comparison with Archon/Hephaestus](./COMPARISON.md)

---

## References

### Inspirational Projects
- **Archon Project**: https://github.com/coleam00/Archon
- **Hephaestus Project**: https://github.com/Ido-Levi/Hephaestus
- **Model Context Protocol**: https://modelcontextprotocol.io/

### Technology Foundations
- **Supabase**: https://supabase.com/
- **PostHog**: https://posthog.com/
- **Gitea**: https://gitea.io/
- **Vespa Search**: https://vespa.ai/
- **Neo4j**: https://neo4j.com/

### Standards & Protocols
- **OpenTelemetry**: https://opentelemetry.io/
- **GitHub Actions**: https://docs.github.com/en/actions
- **OCI Spec**: https://opencontainers.org/

---

## Glossary

**Platform Terms**:
- **DevFlow Hub**: AI orchestration and knowledge management product
- **DevFlow Code**: Git hosting, CI/CD, and package registry product
- **DevFlow Runtime**: Complete backend platform (Supabase + deployment + analytics)
- **Universal Package Registry**: Single registry supporting all package managers

**Technical Terms**:
- **MCP**: Model Context Protocol - standardized protocol for AI tool access
- **RAG**: Retrieval-Augmented Generation - AI technique combining search with generation
- **Guardian**: Monitoring system that steers agents back on track
- **Phase**: Logical work type grouping (analysis, implementation, validation)
- **Kanban**: Visual task board system for coordination
- **Vector Store**: Database optimized for semantic search
- **Buildpack**: Automatic detection and build system (e.g., Heroku buildpacks)
- **Feature Flag**: Configuration toggle for gradual feature rollout

---

**Document Version**: 2.0 (Complete Platform Expansion)  
**Status**: Active Development - Ready for Implementation Planning

---

**End of PRD-001**
