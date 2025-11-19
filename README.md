# DevFlow

**The Complete AI-Native Development Platform**

> DevFlow combines AI orchestration, source control, and runtime infrastructure into a single self-hosted platform. It gives AI agents the comprehensive context and tools they need to autonomously build, test, and deploy software.

[![Status](https://img.shields.io/badge/status-architecture%20complete-green)]()
[![Documentation](https://img.shields.io/badge/docs-15%20PRDs-blue)]()
[![License](https://img.shields.io/badge/license-TBD-gray)]()

---

## 🎯 What is DevFlow?

DevFlow is a unified platform comprising three integrated products:

1.  **DevFlow Hub**: The "Brain" – AI orchestration, knowledge management, and adaptive workflows.
2.  **DevFlow Code**: The "Source" – Git hosting, CI/CD, and universal package registry.
3.  **DevFlow Runtime**: The "Infrastructure" – Complete backend (Database, Auth, Storage) and application deployment.

It synthesizes the best capabilities of **Archon** (Knowledge) and **Hephaestus** (Workflows) while adding the essential infrastructure layer (Code + Runtime) to create a vertically integrated stack for AI development.

---

## 🌟 Product Suite

### 🧠 DevFlow Hub
*AI Orchestration & Knowledge*
- **Knowledge Hub**: Web crawling, RAG, and code indexing.
- **Adaptive Workflows**: Semi-structured phases where agents dynamically create tasks.
- **Guardian**: AI monitoring system to keep agents aligned.
- **MCP Gateway**: Standardized interface for Claude Code, OpenCode, and Cursor.

### 💻 DevFlow Code
*Source Control & CI/CD*
- **Git Server**: Self-hosted repositories with AI code review.
- **CI/CD Pipelines**: GitHub Actions-compatible automation.
- **Universal Registry**: Unified storage for npm, pip, Docker, apt, and more.
- **Security**: Integrated vulnerability scanning and secret detection.

### ⚡ DevFlow Runtime
*Backend & Deployment*
- **Backend Services**: Managed PostgreSQL, Auth, Storage, Realtime (Supabase foundation).
- **App Deployment**: Zero-config "git push" deployment (PaaS).
- **Observability**: Unified metrics, logs, and traces.
- **Platform Services**: Advanced Search (Vespa), Graph (Neo4j), and Billing (Stripe).

---

## 📖 Documentation

### Quick Start
- **[Executive Summary](EXECUTIVE_SUMMARY.md)** - The 5-minute overview.
- **[Platform Architecture](docs/PLATFORM_ARCHITECTURE.md)** - Detailed technical design.

### Detailed PRDs
**Core Platform**
- [PRD-001: System Overview](docs/prds/PRD-001-OVERVIEW.md)
- [PRD-007: Secrets Management](docs/prds/PRD-007-SECRETS-MANAGEMENT.md)
- [PRD-008: Deployment Architecture](docs/prds/PRD-008-DEPLOYMENT-ARCHITECTURE.md)
- [PRD-009: AOSentry Integration](docs/prds/PRD-009-AOSENTRY-INTEGRATION.md)

**DevFlow Hub**
- [PRD-002: Knowledge Hub](docs/prds/PRD-002-KNOWLEDGE-HUB.md)
- [PRD-003: Workflow Engine](docs/prds/PRD-003-WORKFLOW-ENGINE.md)
- [PRD-004: MCP Gateway](docs/prds/PRD-004-MCP-GATEWAY.md)
- [PRD-005: UI Dashboard](docs/prds/PRD-005-UI-DASHBOARD.md)
- [PRD-006: Integrations](docs/prds/PRD-006-INTEGRATIONS.md)

**DevFlow Code**
- [PRD-010: DevFlow Code](docs/prds/PRD-010-DEVFLOW-CODE.md)

**DevFlow Runtime**
- [PRD-011: DevFlow Runtime](docs/prds/PRD-011-DEVFLOW-RUNTIME.md)
- [PRD-012: DevFlow Analytics](docs/prds/PRD-012-DEVFLOW-ANALYTICS.md)
- [PRD-013: Platform Services](docs/prds/PRD-013-PLATFORM-SERVICES.md)

**Tools**
- [PRD-014: DevFlow CLI](docs/prds/PRD-014-DEVFLOW-CLI.md)
- [PRD-015: DevFlow Desktop](docs/prds/PRD-015-DEVFLOW-DESKTOP.md)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      DevFlow Platform                        │
│                   ($2.22M over 24 months)                    │
└──────────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  DevFlow Hub  │      │ DevFlow Code  │      │DevFlow Runtime│
│  (Orchestrate)│      │   (Source)    │      │ (Run & Scale) │
├───────────────┤      ├───────────────┤      ├───────────────┤
│ Knowledge Hub │      │ Git Server    │      │ Database (PG) │
│ Workflows     │      │ CI/CD         │      │ Auth & Storage│
│ MCP Gateway   │      │ Registry      │      │ App Deploy    │
│ UI Dashboard  │      │ Security      │      │ Observability │
└───────────────┘      └───────────────┘      └───────────────┘
```

---

## 🚀 Roadmap

- **Phase 1 (Months 1-12)**: **DevFlow Hub MVP**. Knowledge management, workflows, and basic orchestration.
- **Phase 2 (Months 3-18)**: **DevFlow Code**. Git hosting, CI/CD, and package registry.
- **Phase 3 (Months 1-24)**: **DevFlow Runtime**. Complete backend services and deployment engine.
- **Phase 4 (Months 19-24)**: **Analytics & Polish**. Advanced analytics, desktop app, and enterprise hardening.

---

## 📞 Contact & Community

- **Status**: Architecture Design Complete
- **Next Step**: Phase 1 Implementation
- **Contribution**: See [PRD Index](docs/prds/README.md) to review specifications.

---

<div align="center">

**DevFlow**: Where AI agents have comprehensive context and workflows adapt to reality.

[📖 Read the Docs](docs/prds/README.md) • [🎯 Executive Summary](EXECUTIVE_SUMMARY.md)

</div>
