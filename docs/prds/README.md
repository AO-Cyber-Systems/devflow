# DevFlow Product Requirements Documents (PRDs)

**Project**: DevFlow - Adaptive AI Development Orchestration Platform  
**Version**: 1.0  
**Status**: Draft  
**Last Updated**: November 18, 2025

---

## Overview

This directory contains the comprehensive Product Requirements Documents for DevFlow, a next-generation development workflow orchestration platform that synthesizes the best capabilities of Archon (knowledge management + MCP server) and Hephaestus (adaptive semi-structured workflows).

---

## Document Structure

### [PRD-001: System Overview](./PRD-001-OVERVIEW.md)
**Executive Summary & Architecture**

The foundational document that establishes:
- Project vision and goals
- Core principles and architecture
- Technology stack decisions
- Success metrics and roadmap
- High-level system design

**Key Concepts**:
- Semi-structured workflows with phase-based discovery
- Knowledge-driven execution with RAG
- Unified orchestration layer
- Microservices architecture

**Target Audience**: All stakeholders, technical and non-technical

---

### [PRD-002: Knowledge Hub Service](./PRD-002-KNOWLEDGE-HUB.md)
**Intelligent Knowledge Management**

Detailed specification for the knowledge repository service:
- Web crawling with sitemap detection
- Document processing (PDF, Word, Markdown, Code)
- Vector search with multiple RAG strategies
- Code example extraction and indexing
- Source management and organization

**Key Features**:
- Semantic search with hybrid ranking
- Intelligent chunking strategies
- Multi-format document support
- Real-time knowledge updates

**Technical Stack**: FastAPI, Qdrant, PostgreSQL, PGVector

---

### [PRD-003: Adaptive Workflow Engine](./PRD-003-WORKFLOW-ENGINE.md)
**Self-Building Workflows**

Specification for the semi-structured workflow orchestration:
- Phase system (analysis, implementation, validation)
- Dynamic task creation by agents
- Kanban board coordination
- Guardian monitoring system
- Agent runtime with Git worktree isolation

**Key Innovation**: Workflows that adapt in real-time based on agent discoveries, not pre-planned scenarios.

**Core Components**:
- Phase definitions with done criteria
- Task spawning in any phase
- Kanban-based coordination
- Guardian coherence monitoring

**Technical Stack**: FastAPI, PostgreSQL, tmux, Git worktrees

---

### [PRD-004: MCP Gateway Service](./PRD-004-MCP-GATEWAY.md)
**Unified Model Context Protocol Interface**

Specification for the MCP server that provides standardized tool access:
- Knowledge tools (search, code examples, sources)
- Workflow tools (create/update tasks, phases, Kanban)
- Memory tools (save/query agent memories)
- Agent coordination tools (status, messaging)

**Protocol Support**:
- SSE (Server-Sent Events) for web clients
- stdio for CLI tools (Claude Code, OpenCode)
- Tool registry with schema validation

**Client Compatibility**: Claude Code, OpenCode, Cursor, Windsurf, Claude Desktop

---

### [PRD-005: Unified UI Dashboard](./PRD-005-UI-DASHBOARD.md)
**Comprehensive Control Plane**

Specification for the web-based user interface:
- Dashboard with system overview
- Knowledge Hub browser and search
- Workflow visualizer with Kanban board
- Agent monitor with real-time trajectories
- Settings and configuration

**Technology**: React, TypeScript, Vite, TailwindCSS, Zustand, Socket.IO

**Key Views**:
- Dashboard (metrics, activity feed)
- Knowledge Hub (sources, search, upload)
- Workflows (phases, Kanban, dependency graph)
- Agent Monitor (trajectories, Guardian alerts)
- Settings (API keys, configuration, health)

---

### [PRD-006: SDLC Tool Integrations](./PRD-006-INTEGRATIONS.md)
**Atlassian & GitHub Integration**

Specification for bidirectional sync with external SDLC tools:
- Atlassian Integration (Jira, Confluence, Bitbucket)
- GitHub Integration (Issues, PRs, Projects, Discussions)
- User-level OAuth authentication
- Type hierarchy enforcement (PRD → Epic → Story → Task → Subtask)
- Conflict resolution dashboard
- Webhook-based real-time sync

**Key Capabilities**:
- OAuth 2.0 authentication per user
- Bidirectional sync with hierarchy enforcement
- Automatic custom field creation in Jira
- Confluence as first-class knowledge source
- GitHub Projects integration with Kanban
- Comprehensive conflict resolution UI

**Priority**: Atlassian-first, then GitHub as secondary/supplement

---

### [PRD-007: Secrets & Environment Management](./PRD-007-SECRETS-MANAGEMENT.md)
**1Password Integration & Environment Variables**

Specification for secure secrets management across deployment modes:
- 1Password Connect Server integration (recommended)
- .env file fallback (always supported)
- Per-project environment variables
- Secret rotation workflows
- Three-tier secret model (system, user, project)

**Key Features**:
- Priority cascade: 1Password → .env → ENV
- Encrypted storage for OAuth tokens
- Audit logging of secret access
- Compliance support (SOC2, HIPAA, GDPR)
- Developer onboarding workflows

**Security**: AES-256 encryption, automatic rotation, audit trails

---

### [PRD-008: Deployment Architecture](./PRD-008-DEPLOYMENT-ARCHITECTURE.md)
**Local, SaaS, and On-Premise Deployments**

Specification for flexible deployment options:
- **Local Dev**: Docker required (PostgreSQL + Qdrant)
- **SaaS**: devflow.aocodex.ai (managed hosting)
- **On-Premise**: Docker Compose (corporate deployments)
- **Dedicated Cloud**: Isolated managed instances

**Deployment Modes**:
- Local development with lightweight UI
- SaaS with multi-tenant isolation
- On-premise behind corporate firewalls
- Hybrid mode (local agents + hosted services)

**Key Decisions**:
- Docker as default (no SQLite fallback)
- SaaS-first implementation priority
- VPN and firewall support
- Migration paths between modes

**Technical Stack**: Docker, Kubernetes, PostgreSQL, Qdrant, Nginx

---

### [PRD-009: AOSentry Integration](./PRD-009-AOSENTRY-INTEGRATION.md)
**Unified LLM Gateway**

Specification for routing all LLM operations through AOSentry:
- OpenAI API compatibility (drop-in replacement)
- Automatic retry and fallback
- Intelligent caching and cost optimization
- Multi-provider support (OpenAI, Anthropic, OpenRouter, etc.)
- On-premise LLM routing

**Key Benefits**:
- Single API key for all LLM access
- Cost tracking per project/workflow
- Automatic model routing (cost vs performance)
- Prompt safety and filtering
- Token usage analytics

**AOSentry Features Leveraged**:
- Automatic caching (30%+ cost savings)
- Retry/fallback handling (99.9% success rate)
- Budget controls and alerts
- On-prem LLM support (Ollama, vLLM)

---

## System Architecture

### High-Level Overview

```
┌──────────────────────────────────────────────────────────┐
│                    DevFlow Platform                      │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ Knowledge  │  │  Workflow  │  │   Agent    │        │
│  │    Hub     │◄─┤   Engine   │◄─┤  Runtime   │        │
│  │            │  │            │  │            │        │
│  │ - Crawling │  │ - Phases   │  │ - Spawning │        │
│  │ - Docs     │  │ - Tasks    │  │ - Isolation│        │
│  │ - Search   │  │ - Kanban   │  │ - Guardian │        │
│  │ - RAG      │  │ - Guardian │  │            │        │
│  └────────────┘  └────────────┘  └────────────┘        │
│         │               │               │               │
│         └───────────────┼───────────────┘               │
│                         │                               │
│                ┌────────────────┐                       │
│                │  MCP Gateway   │                       │
│                │                │                       │
│                │ - Knowledge    │                       │
│                │ - Workflow     │                       │
│                │ - Memory       │                       │
│                │ - Coordination │                       │
│                └────────────────┘                       │
│                         │                               │
└─────────────────────────┼───────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
    │  Claude │      │OpenCode │     │ Cursor  │
    │  Code   │      │         │     │         │
    └─────────┘      └─────────┘     └─────────┘

                ┌────────────────┐
                │   UI Dashboard │
                │                │
                │ - Knowledge    │
                │ - Workflows    │
                │ - Agents       │
                │ - Settings     │
                └────────────────┘
```

### Service Communication

**HTTP/REST**: 
- UI ↔ All services
- MCP Gateway ↔ Backend services

**WebSocket/Socket.IO**:
- UI ↔ Backend services (real-time updates)
- Agent trajectories, task updates, Guardian alerts

**gRPC**:
- Services ↔ Qdrant (vector operations)

**MCP Protocol**:
- AI Agents ↔ MCP Gateway
- SSE or stdio transport

---

## Key Innovations

### 1. Semi-Structured Workflows

**Traditional Approach** (Rigid):
```
Task 1 (fixed prompt) → Task 2 (fixed prompt) → Task 3 (fixed prompt)
```

**DevFlow Approach** (Adaptive):
```
Phase 1 (guidelines) → Agent discovers → Creates Phase 2 tasks
                    ↓
Phase 2 (guidelines) → Agent discovers → Creates Phase 1/3 tasks
                    ↓
Phase 3 (guidelines) → Agent discovers → Creates Phase 2 tasks (fixes)
```

**Benefit**: Workflows adapt based on what agents actually find, not what you predicted upfront.

### 2. Knowledge-Driven Execution

Every agent has access to:
- Comprehensive documentation (crawled websites, uploaded docs)
- Code examples from the knowledge base
- Previous agent discoveries (saved memories)
- Project-specific patterns and conventions

**Benefit**: Agents make informed decisions based on project context, not just general LLM knowledge.

### 3. Kanban Coordination

Multiple agents work in parallel without chaos:
- Tasks tracked on Kanban board
- Blocking relationships prevent conflicts
- Agents claim tasks from Ready column
- Status flows: Backlog → Ready → In Progress → Review → Done

**Benefit**: Prevents duplicate work, coordinates dependencies, provides visibility.

### 4. Guardian Monitoring

Continuous monitoring system ensures agents stay on track:
- Analyzes agent trajectories every 60 seconds
- Scores alignment (coherence) with phase goals
- Intervenes when agents drift off course
- Steers agents back to mandatory steps

**Benefit**: Maintains quality without manual supervision.

### 5. Git Worktree Isolation

Each agent works in isolated environment:
- Separate Git worktree (independent file copy)
- Separate tmux session (isolated terminal)
- Changes don't conflict with other agents
- Easy rollback if something goes wrong

**Benefit**: Safe parallel execution with conflict prevention.

---

## Development Phases

### Phase 1: MVP (Q1 2025)
**Goal**: Working system with core features

**Deliverables**:
- ✅ Knowledge Hub: Crawl websites, upload docs, search
- ✅ Workflow Engine: 3-phase system, task creation, Kanban
- ✅ MCP Gateway: Essential tools for knowledge and workflow
- ✅ UI Dashboard: Basic views for all core features
- ✅ Agent Runtime: tmux + worktree isolation
- ✅ Guardian: Basic monitoring and intervention

**Success Criteria**:
- Can ingest and search documentation
- Can run end-to-end workflow (PRD → Code)
- Agents coordinate via Kanban board
- Guardian prevents obvious drift

### Phase 2: Enhancement (Q2 2025)
**Goal**: Advanced features and reliability

**Deliverables**:
- ⬜ Advanced RAG: Hybrid search, reranking, contextual embeddings
- ⬜ Workflow Templates: Pre-built configurations
- ⬜ Enhanced Guardian: Learning from interventions
- ⬜ Observability: Metrics, tracing, analytics
- ⬜ Integration: GitHub, Slack, webhooks

**Success Criteria**:
- Search relevance > 90%
- Workflow success rate > 80%
- Guardian intervention success > 90%

### Phase 3: Enterprise (Q3 2025)
**Goal**: Production-ready for teams

**Deliverables**:
- ⬜ Multi-tenancy: Team workspaces
- ⬜ SSO & RBAC: Enterprise auth
- ⬜ Scalability: Horizontal scaling, distributed queue
- ⬜ Security: Encryption, audit logs
- ⬜ Compliance: SOC2, GDPR

**Success Criteria**:
- Support 100+ concurrent users
- 99.9% uptime
- Enterprise security certifications

---

## Technology Decisions

### Backend
- **Language**: Python 3.10+ (ecosystem, ML libraries, async support)
- **Framework**: FastAPI (modern, async, auto-docs, WebSocket)
- **Database**: PostgreSQL + PGVector (relational + vector search)
- **Vector Store**: Qdrant (fast, scalable, open-source)
- **Task Queue**: Redis + Celery (async processing)
- **Real-time**: Socket.IO (cross-platform WebSocket)

### Frontend
- **Framework**: React 18 + TypeScript (ecosystem, type safety)
- **Build**: Vite (fast HMR, modern tooling)
- **Styling**: TailwindCSS (utility-first, rapid development)
- **State**: Zustand (simple, no boilerplate) + React Query (server state)
- **Viz**: D3.js (graphs), Mermaid (diagrams)

### Infrastructure
- **Containers**: Docker (consistent environments)
- **Orchestration**: Docker Compose (dev), Kubernetes (prod)
- **Monitoring**: Prometheus + Grafana (metrics, alerting)
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: OpenTelemetry (distributed tracing)

### AI/ML
- **LLM Providers**: OpenAI, Anthropic, OpenRouter
- **Embeddings**: OpenAI text-embedding-3-large (3072 dims)
- **Agent Runtime**: Claude Code, OpenCode (MCP-compatible CLI tools)
- **Protocol**: Model Context Protocol (standardized tool access)

---

## Success Metrics

### User Success
| Metric | Target | Critical |
|--------|--------|----------|
| Time to first workflow | < 30 min | Yes |
| Knowledge retrieval accuracy | > 90% | Yes |
| Agent task completion rate | > 85% | Yes |
| User satisfaction (NPS) | > 50 | No |

### Technical Performance
| Metric | Target | Critical |
|--------|--------|----------|
| Knowledge search latency (p95) | < 200ms | Yes |
| Workflow coordination latency | < 500ms | Yes |
| Agent spawn time | < 5 sec | No |
| System uptime | > 99.5% | Yes |

### Business Impact
| Metric | Target | Critical |
|--------|--------|----------|
| Reduction in manual coding | > 40% | No |
| Increase in code quality | > 30% | No |
| Developer productivity gain | > 2x | Yes |
| Knowledge reuse rate | > 70% | No |

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM API costs too high | High | Medium | Caching, rate limiting, model selection |
| Agent coordination failures | High | Medium | Robust Guardian, conflict resolution, rollback |
| Knowledge accuracy issues | Medium | Medium | Human validation, quality scoring, source verification |
| Scaling challenges | High | Low | Microservices from start, horizontal scaling design |
| Security vulnerabilities | High | Low | Security audits, sandboxed execution, access controls |
| User adoption barriers | Medium | Medium | Comprehensive docs, examples, onboarding flow |

---

## Open Questions

### Technical
1. **Agent Isolation Depth**: tmux/worktree sufficient or need containers/VMs?
2. **Knowledge Versioning**: How to handle knowledge base evolution?
3. **Workflow Persistence**: Should workflows survive system restarts?
4. **Conflict Resolution**: How to handle git merge conflicts automatically?

### Product
1. **Deployment Model**: Self-hosted vs. cloud-hosted priority?
2. **Pricing Strategy**: Open source + commercial features? SaaS subscription?
3. **Enterprise Features**: Which features justify enterprise tier?

### Business
1. **Go-to-Market**: Developer-led growth or enterprise sales?
2. **Community Building**: Open source community strategy?
3. **Competition**: How to differentiate from GitHub Copilot Workspace, Cursor, Windsurf?

---

## Reference Materials

### Inspirational Projects
- **Archon**: https://github.com/coleam00/Archon
  - Knowledge management via MCP
  - RAG strategies
  - Task management integration
  
- **Hephaestus**: https://github.com/Ido-Levi/Hephaestus
  - Semi-structured workflows
  - Guardian monitoring
  - Kanban coordination
  - Phase-based discovery

### Standards & Protocols
- **Model Context Protocol**: https://modelcontextprotocol.io/
- **OpenTelemetry**: https://opentelemetry.io/
- **REST API Design**: https://restfulapi.net/

### Technology Documentation
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Qdrant**: https://qdrant.tech/documentation/
- **PGVector**: https://github.com/pgvector/pgvector

---

## Glossary

**Terms used across PRDs**:

- **Agent**: AI instance running in isolated environment (tmux + worktree)
- **Coherence**: Measure of agent alignment with phase goals (0.0-1.0)
- **Guardian**: Monitoring system that steers agents back on track
- **Kanban**: Visual board for tracking tasks (Backlog → Ready → In Progress → Review → Done)
- **MCP (Model Context Protocol)**: Standard protocol for AI tool access
- **Phase**: Logical grouping of work types (analysis, implementation, validation)
- **RAG (Retrieval-Augmented Generation)**: AI technique combining search with generation
- **Task**: Specific piece of work created dynamically by agents
- **Trajectory**: Sequence of agent actions (for Guardian monitoring)
- **Vector Store**: Database optimized for semantic similarity search
- **Worktree**: Git feature creating independent working copy of repository

---

## Document History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-18 | 1.0 | Initial PRD series (PRD-001 through PRD-006) created | DevFlow Team |
| 2025-11-18 | 1.1 | Added PRD-007 (Secrets), PRD-008 (Deployment), PRD-009 (AOSentry) | DevFlow Team |

---

## Feedback & Contributions

These PRDs are living documents. We welcome feedback, questions, and suggestions.

**How to contribute**:
1. Open an issue for discussion
2. Submit a PR with proposed changes
3. Join our Discord for real-time discussion

**What we're looking for**:
- Technical feedback on architecture decisions
- User experience insights
- Missing requirements or edge cases
- Clarification requests

---

**Next Steps**:
1. Review all 9 PRDs
2. Discuss and refine open questions
3. Prioritize Phase 1 features
4. Begin technical design documents
5. Set up development environment
6. Start MVP implementation
7. Configure secrets management (1Password or .env)
8. Choose deployment mode (Local, SaaS, or On-Prem)
9. Set up AOSentry integration

---

**End of PRD Index**
