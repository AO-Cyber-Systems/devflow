# DevFlow

**Adaptive AI Development Orchestration Platform**

> DevFlow combines comprehensive knowledge management with self-building workflows to enable truly autonomous AI-powered software development.

[![Status](https://img.shields.io/badge/status-planning-blue)]()
[![License](https://img.shields.io/badge/license-TBD-gray)]()
[![Documentation](https://img.shields.io/badge/docs-comprehensive-green)]()

---

## 🎯 What is DevFlow?

DevFlow is a next-generation platform that synthesizes the best capabilities from two leading open-source projects:

- **[Archon](https://github.com/coleam00/Archon)**: Knowledge management and MCP server capabilities
- **[Hephaestus](https://github.com/Ido-Levi/Hephaestus)**: Adaptive semi-structured workflow execution

The result is a comprehensive orchestration platform where AI agents have access to all project knowledge and can dynamically adapt their workflows based on real-time discoveries.

---

## 🌟 Key Features

### 📚 Comprehensive Knowledge Hub
- **Web Crawling**: Automatic sitemap detection and documentation ingestion
- **Document Processing**: PDF, Word, Markdown, Code with intelligent chunking
- **Advanced Search**: Semantic search with hybrid ranking and LLM reranking
- **Code Examples**: Automatic extraction and indexing of code patterns
- **Real-time Updates**: Live synchronization as knowledge evolves

### 🔄 Adaptive Workflow Engine
- **Semi-Structured Phases**: Define work types, not specific tasks
- **Dynamic Task Creation**: Agents spawn tasks based on discoveries
- **Kanban Coordination**: Visual board prevents conflicts and duplication
- **Guardian Monitoring**: AI system ensures agents stay on track
- **Git Worktree Isolation**: Safe parallel execution with automatic conflict prevention

### 🔌 Unified MCP Gateway
- **Single Interface**: Access knowledge and workflows through Model Context Protocol
- **Comprehensive Tools**: Search, task management, memory storage, coordination
- **Multi-Client Support**: Claude Code, OpenCode, Cursor, Windsurf, and more
- **Standardized Protocol**: SSE and stdio transport modes

### 🎨 Unified UI Dashboard
- **Real-time Monitoring**: Live agent trajectories and task updates
- **Knowledge Browser**: Search and explore project documentation
- **Workflow Visualizer**: Kanban board and dependency graphs
- **Agent Observability**: Guardian alerts and coherence scoring
- **System Configuration**: Centralized settings and health monitoring

---

## 🚀 The Core Innovation

### Traditional Approach (Rigid)
```
Developer predicts scenarios → Defines every task → Agents execute
❌ Breaks when reality diverges from predictions
```

### DevFlow Approach (Adaptive)
```
Developer defines phases → Agents discover needs → Create tasks dynamically
✅ Workflows adapt based on actual discoveries
```

### Example: Self-Building Workflow

```
Phase 1 Agent analyzes requirements
    ↓
Creates 5 implementation tasks (parallel)
    ↓
Phase 2 Agents build components
    ↓
Phase 3 Agent discovers optimization opportunity
    ↓
Creates NEW Phase 1 investigation task
    ↓
Investigation confirms viability
    ↓
Creates Phase 2 implementation task
    ↓
Workflow adapted itself!
```

**The workflow branched based on what agents actually found, not what was predicted upfront.**

---

## 📖 Documentation

### Quick Start
- **[Executive Summary](EXECUTIVE_SUMMARY.md)** - High-level overview (5 min read)
- **[PRD Index](docs/prds/README.md)** - Complete documentation roadmap

### Detailed PRDs
1. **[PRD-001: System Overview](docs/prds/PRD-001-OVERVIEW.md)** - Vision, architecture, technology stack
2. **[PRD-002: Knowledge Hub](docs/prds/PRD-002-KNOWLEDGE-HUB.md)** - Crawling, documents, search, RAG
3. **[PRD-003: Workflow Engine](docs/prds/PRD-003-WORKFLOW-ENGINE.md)** - Phases, tasks, Kanban, Guardian
4. **[PRD-004: MCP Gateway](docs/prds/PRD-004-MCP-GATEWAY.md)** - Protocol, tools, integrations
5. **[PRD-005: UI Dashboard](docs/prds/PRD-005-UI-DASHBOARD.md)** - Views, components, real-time updates
6. **[PRD-006: SDLC Tool Integrations](docs/prds/PRD-006-INTEGRATIONS.md)** - Atlassian, GitHub, bidirectional sync

### Analysis
- **[Comparison Document](docs/prds/COMPARISON.md)** - Detailed synthesis of Archon + Hephaestus

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                DevFlow Platform                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐│
│  │  Knowledge   │  │   Workflow   │  │   Agent   ││
│  │     Hub      │◄─┤    Engine    │◄─┤  Runtime  ││
│  │              │  │              │  │           ││
│  │ - Crawling   │  │ - Phases     │  │ - Spawn   ││
│  │ - Documents  │  │ - Tasks      │  │ - Isolate ││
│  │ - Search/RAG │  │ - Kanban     │  │ - Monitor ││
│  └──────────────┘  │ - Guardian   │  └───────────┘│
│                    └──────────────┘                 │
│                           │                         │
│                  ┌────────▼────────┐               │
│                  │  MCP Gateway    │               │
│                  │  (Port 8051)    │               │
│                  └────────▲────────┘               │
└───────────────────────────┼──────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
   │ Claude  │        │OpenCode │        │ Cursor  │
   │  Code   │        │         │        │         │
   └─────────┘        └─────────┘        └─────────┘
```

**Microservices Architecture**: Independent, scalable services with HTTP/WebSocket communication

---

## 🛠️ Technology Stack

### Backend
- **Python 3.10+** - Language
- **FastAPI** - Web framework (async, modern)
- **PostgreSQL + PGVector** - Database with vector search
- **Qdrant** - Vector store for embeddings
- **Redis + Celery** - Task queue for background jobs
- **Socket.IO** - Real-time updates

### Frontend
- **React 18 + TypeScript** - UI framework with type safety
- **Vite** - Build tool (fast HMR)
- **TailwindCSS** - Utility-first styling
- **Zustand** - State management
- **React Query** - Server state management
- **D3.js / Mermaid** - Visualizations

### AI/ML
- **OpenAI, Anthropic, OpenRouter** - LLM providers
- **text-embedding-3-large** - Embeddings (3072 dimensions)
- **Claude Code, OpenCode** - Agent runtime tools
- **Model Context Protocol** - Standardized tool access

### Infrastructure
- **Docker** - Containerization
- **Docker Compose / Kubernetes** - Orchestration
- **Prometheus + Grafana** - Monitoring
- **ELK Stack** - Logging
- **OpenTelemetry** - Tracing

---

## 📊 Success Metrics

### User Success
- ⏱️ Time to first workflow: **< 30 minutes**
- 🎯 Knowledge retrieval accuracy: **> 90%**
- ✅ Agent task completion rate: **> 85%**
- 😊 User satisfaction (NPS): **> 50**

### Technical Performance
- ⚡ Knowledge search latency (p95): **< 200ms**
- 🔄 Workflow coordination latency: **< 500ms**
- 🚀 Agent spawn time: **< 5 seconds**
- 📈 System uptime: **> 99.5%**

### Business Impact
- 📉 Reduction in manual coding: **> 40%**
- 🐛 Increase in code quality: **> 30%**
- 🚀 Developer productivity gain: **> 2x**
- 📚 Knowledge reuse rate: **> 70%**

---

## 🗺️ Roadmap

### Phase 1: MVP (Q1 2025) - 6 months
**Goal**: Working system with core features

✅ Knowledge Hub (crawl, upload, search)  
✅ Workflow Engine (phases, tasks, Kanban, Guardian)  
✅ MCP Gateway (essential tools)  
✅ UI Dashboard (basic views)  
✅ Agent Runtime (isolation)

### Phase 2: Enhancement (Q2 2025) - 3 months
**Goal**: Advanced features and reliability

⬜ Advanced RAG strategies  
⬜ Workflow templates  
⬜ Enhanced observability  
⬜ Integration ecosystem (GitHub, Slack)

### Phase 3: Enterprise (Q3 2025) - 3 months
**Goal**: Production-ready for teams

⬜ Multi-tenancy  
⬜ SSO & RBAC  
⬜ Horizontal scaling  
⬜ Security certifications (SOC2, GDPR)

---

## 🆚 Competitive Positioning

| Platform | DevFlow | Archon | Hephaestus | GitHub Copilot | Cursor |
|----------|---------|--------|------------|----------------|--------|
| Knowledge Management | ✅ Full | ✅ Full | ❌ | ❌ | ⚠️ Basic |
| Adaptive Workflows | ✅ Full | ❌ | ✅ Full | ❌ | ❌ |
| Multi-Agent Coordination | ✅ Kanban + Guardian | ⚠️ Basic | ✅ Kanban + Guardian | ❌ | ❌ |
| MCP Server | ✅ Unified | ✅ Basic | ✅ Basic | ❌ | ❌ |
| Enterprise Features | 🔄 Planned | 🔄 Planned | ❌ | ✅ Full | ⚠️ Basic |

**Unique Value**: Only platform combining comprehensive knowledge management with adaptive workflow execution

---

## 🤝 Contributing

We welcome contributions! This project is currently in the planning phase.

**Ways to contribute**:
- 📝 Review and provide feedback on PRDs
- 💡 Suggest features or improvements
- 🐛 Report issues or concerns
- 📖 Improve documentation
- 💻 Code contributions (coming soon)

**Getting started**:
1. Read the [Executive Summary](EXECUTIVE_SUMMARY.md)
2. Review the [PRD Index](docs/prds/README.md)
3. Join our [Discord](#) (link TBD)
4. Open an issue or discussion

---

## 📄 License

License TBD - Under consideration:
- Archon Community License (ACL) - Similar to Archon
- AGPL-3.0 - Similar to Hephaestus
- Dual licensing (Open source + Commercial)

---

## 🙏 Acknowledgments

DevFlow builds upon the excellent work of:

- **[Archon](https://github.com/coleam00/Archon)** by [@coleam00](https://github.com/coleam00)
  - Knowledge management architecture
  - MCP server implementation
  - Microservices design patterns

- **[Hephaestus](https://github.com/Ido-Levi/Hephaestus)** by [@Ido-Levi](https://github.com/Ido-Levi)
  - Semi-structured workflow system
  - Guardian monitoring approach
  - Kanban coordination patterns

Thank you to both projects for demonstrating what's possible with AI agent orchestration.

---

## 📞 Contact

**Status**: Planning Phase

For questions, feedback, or collaboration:
- **GitHub Issues**: [Report bugs or request features]
- **Discussions**: [Ask questions or share ideas]
- **Discord**: [Community server] (TBD)
- **Email**: [Contact email] (TBD)

---

## 📚 Additional Resources

### Inspiration Projects
- [Archon](https://github.com/coleam00/Archon) - 13.2k ⭐
- [Hephaestus](https://github.com/Ido-Levi/Hephaestus) - 983 ⭐
- [Model Context Protocol](https://modelcontextprotocol.io/)

### Related Technologies
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Qdrant](https://qdrant.tech/)
- [PGVector](https://github.com/pgvector/pgvector)
- [PydanticAI](https://ai.pydantic.dev/)

---

## 📈 Project Stats

**Documentation**: 5,773 lines across 8 documents  
**PRDs**: 5 comprehensive specifications  
**Status**: Planning & Design Phase  
**Target**: MVP Q1 2025

---

<div align="center">

**DevFlow: Where AI agents have comprehensive context and workflows adapt to reality.**

*"The only platform that combines the knowledge your agents need with the flexibility they require."*

[📖 Read the Docs](docs/prds/README.md) • [🎯 Executive Summary](EXECUTIVE_SUMMARY.md) • [🤝 Contribute](#contributing)

</div>

---

**Last Updated**: November 18, 2025  
**Version**: 1.0 (Planning Phase)
