# DevFlow Architectural Assessment (v2.1)

**Date:** November 18, 2025
**Status:** Updated based on Feedback & Supabase Docs Analysis
**Scope:** PRDs 001-015, Deployment Architecture, Integration Strategy

---

## 1. Strategic Pivots

### 1.1. Local Environment Optimization
**Decision:** The local development environment (`devflow up`) will **not** include the heavy "DevFlow Code" (Git Server) stack.
**Rationale:** Developer experience is paramount. Local resources should be reserved for the "Inner Loop" (Coding, Running App, Testing Agents). Source control and CI/CD are "Outer Loop" concerns best handled by a remote server (SaaS or On-Prem).

### 1.2. Gitea Strategy: "Headless Engine"
**Decision:** Fork Gitea but treat it primarily as a backend engine.
**Rationale:** Building a Git host from scratch is a multi-year risk. Gitea provides the critical plumbing (Git protocol, SSH, Auth). The "DevFlow" value add is the **AI-Native Experience**, which will be built as a custom UI layer interacting with the Gitea API, rather than modifying Gitea's native templates.

### 1.3. AOSentry Deployment
**Decision:** AOSentry is a deployable artifact (`aocodex/aosentry`), not just a SaaS endpoint.
**Rationale:** Enables true air-gapped enterprise deployments while maintaining a unified API contract for agents.

## 2. Supabase Integration Analysis

### 2.1. Multi-Project Architecture
**Finding:** Supabase's own analysis recommends a **Hybrid Architecture** (Database-per-project + Shared Services).
**Adoption:** DevFlow Runtime will adopt this exact model for its SaaS/Enterprise edition.
- **SaaS/Enterprise:** Multi-tenant (Shared Services + Isolated DBs).
- **Local:** Single-tenant (Simulated stack).

### 2.2. Missing Features in Self-Hosted
**Finding:** Standard Supabase self-hosted lacks **Billing**, **Organization Management**, and **Multi-Project UI**.
**Mitigation:**
- **Billing:** Covered by `PRD-013` (Stripe Integration).
- **Org Management:** To be built as part of DevFlow Hub's "Platform Layer".
- **UI:** The Supabase Studio codebase contains ~80% of the required multi-project UI code behind feature flags. We can leverage this.

## 3. Implementation Recommendations

### 3.1. DevFlow Code Implementation
*   **Recommendation:** Start by deploying Gitea stock. Build the "DevFlow Code UI" as a separate React app that talks to the Gitea API. Only fork/modify Gitea internals when API limitations are hit (e.g., for deep AI hook integration).

### 3.2. Runtime "Local vs. Prod" Parity
*   **Recommendation:** Ensure the Local Docker stack uses the *exact same* service images as the Production stack, just configured for single-tenancy. This minimizes "it works on my machine" issues.

### 3.3. Analytics Strategy
*   **Recommendation:** For Phase 1 (MVP), rely on Supabase's built-in analytics (pg_stat_statements, log analysis). Defer the PostHog fork (`PRD-012`) until Phase 3/4 when advanced product analytics (feature flags/session replay) become the priority.

## 4. Updated Roadmap Alignment

1.  **Phase 1 (MVP):**
    *   **Hub:** Knowledge + Workflow + Agents.
    *   **Runtime:** Local Docker stack (Supabase).
    *   **Code:** Remote Gitea instance (Stock).
    *   **Goal:** An agent can read docs, plan a task, write code, and push to Git.

2.  **Phase 2 (Platform):**
    *   **Code:** Custom AI-native UI for Gitea.
    *   **Runtime:** Multi-tenant SaaS deployment.
    *   **Goal:** Teams can onboard and manage projects.

3.  **Phase 3 (Enterprise):**
    *   **AOSentry:** On-prem deployment.
    *   **Analytics:** PostHog fork.
    *   **Goal:** Air-gapped, compliance-ready deployment.

**Signed:**
Opencode Agent
November 18, 2025
