# PRD-010: DevFlow Code

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)  
**Investment:** $540,000 over 18 months

---

## Executive Summary

DevFlow Code is a complete source code and artifact management platform providing Git hosting, CI/CD pipelines, and a universal package registry. Built on a Gitea fork enhanced with AI-powered code review, DevFlow Code supports all major package managers (npm, pip, Docker, apt, cargo, etc.) in a single unified registry.

**Key Innovation**: Universal package registry supporting language packages (npm, pip), OS packages (apt, yum), containers (Docker), and ML models (ONNX, TensorFlow) in one system.

---

## Goals

### Primary Goals

1. **Self-Hosted Git Alternative**: Complete replacement for GitHub/GitLab with data sovereignty
2. **AI-Enhanced Code Review**: Intelligent pull request analysis integrated with DevFlow Hub knowledge
3. **Universal Package Registry**: Single registry for all package types and formats
4. **GitHub Actions Compatible**: Existing workflows run without modification
5. **Seamless Integration**: Automatic configuration with DevFlow Hub and Runtime

### Secondary Goals

1. Project management (issues, boards, milestones)
2. Security scanning and vulnerability detection
3. Dependency graph analysis with Neo4j integration
4. Branch protection and merge policies
5. Code metrics and quality analysis

---

## Investment Breakdown

**Total**: $540,000 over 18 months

| Component | Cost | Duration | Priority |
|-----------|------|----------|----------|
| Git Server (Gitea fork) | $100k | 6 months | P0 |
| CI/CD System | $80k | 4 months | P0 |
| AI Code Review | $120k | 4 months | P0 |
| Universal Package Registry | $140k | 6 months | P0 |
| Project Management | $60k | 3 months | P1 |
| Integration & Polish | $40k | 2 months | P1 |

**Timeline**:
- Month 3-9: Git Server + CI/CD foundation
- Month 6-10: AI Code Review
- Month 9-15: Universal Package Registry
- Month 12-15: Project Management
- Month 16-18: Integration & Polish

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DevFlow Code                              │
│                     ($540k over 18 months)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Git Server  │    │   CI/CD      │    │   Package    │
│  (Gitea++)   │───►│   Engine     │───►│   Registry   │
│              │    │              │    │              │
│ - Repos      │    │ - Pipelines  │    │ - npm/pip    │
│ - PRs        │    │ - Runners    │    │ - Docker     │
│ - Branches   │    │ - Actions    │    │ - apt/yum    │
│ - Webhooks   │    │ - Artifacts  │    │ - cargo/gem  │
│              │    │              │    │ - ML models  │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌──────────────────┐
                    │  AI Code Review  │
                    │   (via Hub)      │
                    ├──────────────────┤
                    │ - Diff analysis  │
                    │ - Pattern detect │
                    │ - Best practices │
                    │ - Security scan  │
                    └──────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Project    │    │   Security   │    │ Integration  │
│  Management  │    │   Scanner    │    │    Points    │
├──────────────┤    ├──────────────┤    ├──────────────┤
│ - Issues     │    │ - CVE detect │    │ → Hub (AI)   │
│ - Boards     │    │ - SAST       │    │ → Runtime    │
│ - Milestones │    │ - Dependency │    │ → Analytics  │
│ - Labels     │    │ - Secrets    │    │ → CLI        │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## Architecture Strategy

### The "Engine vs. Experience" Approach

Building a Git hosting platform from scratch is a massive undertaking (Git protocol, SSH, diffs, merge logic). To achieve our goals within a reasonable timeline, DevFlow Code adopts a **Headless Gitea** strategy:

1.  **The Engine (Gitea Fork)**: We fork Gitea to serve as the robust backend engine. It handles:
    *   Git repository storage and protocol (HTTP/SSH).
    *   User authentication and permissions.
    *   Webhooks and event dispatch.
    *   Basic package registry functions.

2.  **The Experience (DevFlow UI)**: We build a custom, AI-native frontend that communicates with the Gitea API. This allows us to:
    *   Inject AI code review directly into the PR flow.
    *   Integrate seamlessly with DevFlow Hub (Kanban/Agents).
    *   Provide a modern, cohesive UX without being constrained by Gitea's server-side rendered templates.

**Deployment Note**: DevFlow Code is designed as a **Server/Cloud Component**. It is not intended to run on a developer's local machine during standard `flow up` operations, preserving local resources for active development tasks (Runtime + Hub).

---

**Repository Management**:
- Unlimited private/public repositories
- Git LFS support for large files
- Repository templates
- Repository mirroring (from GitHub, GitLab)
- Archive and deletion policies

**Branch Management**:
- Protected branches with policies
- Required reviewers
- Status checks before merge
- Branch permissions per team/user
- Auto-delete after merge

**Pull/Merge Requests**:
- Code review workflow
- Inline comments
- Review assignments
- Approval requirements
- Merge strategies (merge, squash, rebase)
- Draft PRs
- PR templates

**Webhooks & Integration**:
- Webhook delivery to external services
- Event filtering (push, PR, issue, etc.)
- Retry logic with exponential backoff
- Webhook secret verification
- Integration with DevFlow Hub workflows

### AI Enhancements

**Automatic PR Analysis**:
- Code complexity scoring
- Breaking change detection
- Test coverage impact
- Performance impact analysis
- Security vulnerability scanning

**Smart Suggestions**:
- Reviewer recommendations (based on file expertise)
- Related PRs and issues
- Documentation updates needed
- Migration guide requirements

### Technical Stack

**Base**: Gitea v1.21+ fork
**Language**: Go 1.21+
**Storage**: Git repositories on filesystem + PostgreSQL metadata
**Cache**: Redis for session and Git protocol optimization
**Protocol**: Git over HTTP/HTTPS and SSH

### Database Schema Extensions

```sql
-- DevFlow-specific extensions to Gitea schema

CREATE TABLE devflow_pr_analysis (
  id BIGSERIAL PRIMARY KEY,
  pr_id BIGINT REFERENCES pull_request(id),
  analysis_version VARCHAR(50),
  complexity_score NUMERIC(5,2),
  breaking_changes JSONB,
  security_findings JSONB,
  performance_impact JSONB,
  test_coverage_delta NUMERIC(5,2),
  ai_summary TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE devflow_repo_sync (
  id BIGSERIAL PRIMARY KEY,
  repo_id BIGINT REFERENCES repository(id),
  hub_project_id UUID, -- DevFlow Hub project
  runtime_app_id UUID, -- DevFlow Runtime app
  auto_deploy BOOLEAN DEFAULT false,
  sync_settings JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### API Extensions

```http
# AI Code Review
POST /api/v1/repos/{owner}/{repo}/pulls/{index}/ai-review
GET  /api/v1/repos/{owner}/{repo}/pulls/{index}/ai-review

# DevFlow Integration
POST /api/v1/repos/{owner}/{repo}/devflow/sync
GET  /api/v1/repos/{owner}/{repo}/devflow/status

# Reviewer Recommendations
GET  /api/v1/repos/{owner}/{repo}/pulls/{index}/suggested-reviewers
```

---

## Component 2: CI/CD Engine ($80k, 4 months)

### Overview

GitHub Actions-compatible CI/CD system with enhanced artifact management and DevFlow Runtime deployment integration.

### Core Features

**Workflow System**:
- YAML-based workflow definitions
- GitHub Actions syntax compatibility
- Reusable workflows
- Composite actions
- Matrix builds
- Conditional execution
- Workflow dependencies

**Runner Management**:
- Self-hosted runners
- Runner groups and labels
- Auto-scaling with Kubernetes
- Docker-based execution
- Resource limits per job
- Runner health monitoring

**Actions Marketplace**:
- Public action registry
- Private action sharing
- Action versioning (git tags)
- Action usage analytics
- Security scanning of actions

**Artifact Management**:
- Build artifact storage
- Artifact retention policies
- Cross-job artifact sharing
- Automatic package publishing
- Direct upload to Package Registry

### GitHub Actions Compatibility

**Supported Events**:
```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    types: [opened, synchronize]
  release:
    types: [published]
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:
  workflow_call:
```

**Supported Contexts**:
- `github.*` - Repository and event data
- `env.*` - Environment variables
- `secrets.*` - Secret access
- `matrix.*` - Matrix strategy
- `needs.*` - Job dependencies
- `runner.*` - Runner information
- `devflow.*` - DevFlow-specific context (NEW)

**DevFlow Extensions**:
```yaml
# Access DevFlow Hub knowledge
- name: Query documentation
  uses: devflow/hub-query@v1
  with:
    query: "deployment best practices"
    
# Deploy to DevFlow Runtime
- name: Deploy to staging
  uses: devflow/runtime-deploy@v1
  with:
    app: my-app
    environment: staging
    
# Publish to Package Registry
- name: Publish package
  uses: devflow/registry-publish@v1
  with:
    type: npm
    access: public
```

### Technical Stack

**Workflow Engine**: Custom (GitHub Actions compatible)
**Job Execution**: Docker containers
**Orchestration**: Kubernetes Jobs
**Queue**: Redis for job queue
**Storage**: PostgreSQL for metadata, S3 for artifacts
**Logs**: Streaming to Loki

### Database Schema

```sql
CREATE TABLE ci_workflows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id BIGINT REFERENCES repository(id),
  name VARCHAR(255),
  path VARCHAR(500), -- .github/workflows/deploy.yml
  content TEXT,
  enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ci_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id UUID REFERENCES ci_workflows(id),
  run_number BIGINT,
  event VARCHAR(50),
  status VARCHAR(20), -- queued, in_progress, completed, failed
  conclusion VARCHAR(20), -- success, failure, cancelled, skipped
  triggered_by BIGINT REFERENCES "user"(id),
  commit_sha VARCHAR(40),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  logs_url TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ci_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID REFERENCES ci_runs(id),
  job_name VARCHAR(255),
  runner_id UUID,
  status VARCHAR(20),
  conclusion VARCHAR(20),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  logs TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ci_artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID REFERENCES ci_runs(id),
  name VARCHAR(255),
  size_bytes BIGINT,
  storage_path TEXT,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Component 3: AI Code Review ($120k, 4 months)

### Overview

Integration with DevFlow Hub to provide intelligent, context-aware code review powered by LLMs and project knowledge.

### Core Features

**Automated Review**:
- Code style and convention checking
- Best practice validation
- Security vulnerability detection
- Performance anti-pattern identification
- Documentation completeness analysis

**Context-Aware Analysis**:
- Project-specific patterns from Hub knowledge
- Historical code review feedback
- Team coding standards
- Framework-specific best practices
- Related code examples

**Review Assistance**:
- Suggested review comments
- Code improvement recommendations
- Test coverage analysis
- Breaking change detection
- Migration path suggestions

### Integration with DevFlow Hub

**Knowledge Sources**:
1. **Project Documentation**: README, CONTRIBUTING, style guides
2. **Historical PRs**: Past review comments and discussions
3. **Code Examples**: Approved patterns from knowledge base
4. **External Docs**: Framework docs, API references
5. **Team Decisions**: ADRs (Architecture Decision Records)

**AI Review Workflow**:

```
PR Created
    ↓
1. Extract diff and context
    ↓
2. Query DevFlow Hub for relevant knowledge
    ↓
3. Analyze code changes with LLM (via AOSentry)
    ↓
4. Generate review comments
    ↓
5. Post comments to PR
    ↓
6. Update knowledge base with findings
```

### Review Types

**Style Review**:
- Naming conventions
- Code formatting
- Comment quality
- Import organization
- File structure

**Logic Review**:
- Algorithm efficiency
- Edge case handling
- Error handling
- Null safety
- Resource management

**Security Review**:
- SQL injection risks
- XSS vulnerabilities
- Authentication issues
- Authorization bypasses
- Sensitive data exposure

**Architecture Review**:
- Design pattern usage
- Dependency direction
- Coupling and cohesion
- SOLID principles
- DRY violations

### Configuration

```yaml
# .devflow/code-review.yml

review:
  enabled: true
  auto_comment: true
  blocking: false  # Require approval before merge
  
  rules:
    - name: Security
      severity: error
      auto_fix: false
      
    - name: Style
      severity: warning
      auto_fix: true
      
    - name: Performance
      severity: info
      auto_fix: false
      
  thresholds:
    complexity_max: 10
    function_length_max: 50
    test_coverage_min: 80
    
  knowledge_sources:
    - project_docs
    - team_standards
    - framework_docs
    
  llm_config:
    model: gpt-4-turbo  # via AOSentry
    temperature: 0.2
    max_tokens: 2000
```

### API

```http
# Trigger AI review
POST /api/v1/repos/{owner}/{repo}/pulls/{index}/ai-review
{
  "review_types": ["style", "logic", "security"],
  "auto_comment": true,
  "blocking": false
}

# Get AI review results
GET /api/v1/repos/{owner}/{repo}/pulls/{index}/ai-review
{
  "status": "completed",
  "findings": [
    {
      "type": "security",
      "severity": "error",
      "file": "app/auth.py",
      "line": 42,
      "message": "SQL injection vulnerability detected",
      "suggestion": "Use parameterized queries",
      "auto_fix_available": false
    }
  ],
  "summary": "3 errors, 5 warnings, 2 info",
  "completed_at": "2025-11-18T10:30:00Z"
}
```

---

## Component 4: Universal Package Registry ($140k, 6 months)

### Overview

Single registry supporting all major package managers - the killer feature that differentiates DevFlow Code from competitors.

### Supported Package Types

#### Language Package Managers

| Manager | Language | Features | Priority |
|---------|----------|----------|----------|
| **npm** | JavaScript/TypeScript | Scopes, dist-tags, workspaces | P0 |
| **pip** | Python | Wheels, source distributions, extras | P0 |
| **cargo** | Rust | Crate registry, sparse index | P0 |
| **gem** | Ruby | Gem packages, versioning | P0 |
| **maven** | Java | POMs, snapshots, releases | P0 |
| **nuget** | C# | Packages, symbols | P0 |
| **composer** | PHP | Composer packages | P1 |
| **go** | Go | Go modules proxy | P1 |
| **hex** | Elixir | Hex packages | P1 |
| **pub** | Dart | Dart/Flutter packages | P1 |
| **cran** | R | R packages | P2 |
| **luarocks** | Lua | Lua modules | P2 |

#### OS Package Managers

| Manager | OS | Features | Priority |
|---------|-----|----------|----------|
| **apt** | Debian/Ubuntu | deb packages, repo metadata | P0 |
| **yum/dnf** | RedHat/Fedora | RPM packages, repodata | P0 |
| **brew** | macOS | Formulas, bottles | P1 |
| **chocolatey** | Windows | nupkg packages | P1 |
| **winget** | Windows | msix, exe, msi | P1 |
| **pacman** | Arch Linux | pkg.tar.zst | P2 |
| **apk** | Alpine | apk packages | P2 |

#### Container & Infrastructure

| Type | Format | Features | Priority |
|------|--------|----------|----------|
| **Docker** | OCI images | Multi-arch, layers, manifests | P0 |
| **Helm** | Charts | Chart repo, dependencies | P0 |
| **OCI Artifacts** | Generic | Any OCI-compatible artifact | P1 |
| **Terraform** | Modules | Module registry | P1 |
| **Vagrant** | Boxes | Box catalog | P2 |

#### ML Models & Data

| Type | Format | Features | Priority |
|------|--------|----------|----------|
| **ONNX** | Models | Model zoo, versioning | P1 |
| **TensorFlow** | SavedModel | Model registry | P1 |
| **PyTorch** | .pt/.pth | Torch hub compatible | P1 |
| **Hugging Face** | Models | Transformers, datasets | P2 |

### Architecture

```
┌───────────────────────────────────────────────────────────┐
│               Universal Package Registry                   │
└───────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Storage   │   │   Metadata  │   │   Protocol  │
│   Layer     │   │   Service   │   │   Adapters  │
├─────────────┤   ├─────────────┤   ├─────────────┤
│ S3/MinIO    │   │ PostgreSQL  │   │ npm API     │
│ Content-    │   │ Package info│   │ pip API     │
│ addressed   │   │ Versions    │   │ Docker API  │
│ blobs       │   │ Dependencies│   │ apt API     │
│ Dedupe      │   │ Downloads   │   │ maven API   │
└─────────────┘   └─────────────┘   └─────────────┘
```

### Storage Strategy

**Content-Addressed Storage**:
- All packages stored by content hash (SHA256)
- Automatic deduplication across package types
- Immutable blobs (never modified, only added)
- Garbage collection for unreferenced blobs

**Metadata Database**:
```sql
CREATE TABLE registry_packages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type VARCHAR(50), -- npm, pip, docker, apt, etc.
  namespace VARCHAR(255), -- @scope, org, etc.
  name VARCHAR(255),
  visibility VARCHAR(20), -- public, private, internal
  repo_id BIGINT REFERENCES repository(id),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(type, namespace, name)
);

CREATE TABLE registry_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  package_id UUID REFERENCES registry_packages(id),
  version VARCHAR(100),
  metadata JSONB, -- package-type-specific metadata
  blob_hash VARCHAR(64), -- SHA256 of package file
  blob_size BIGINT,
  published_by BIGINT REFERENCES "user"(id),
  published_at TIMESTAMP DEFAULT NOW(),
  downloads BIGINT DEFAULT 0,
  UNIQUE(package_id, version)
);

CREATE TABLE registry_blobs (
  hash VARCHAR(64) PRIMARY KEY,
  size_bytes BIGINT,
  storage_path TEXT,
  mime_type VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  last_accessed TIMESTAMP DEFAULT NOW(),
  ref_count INTEGER DEFAULT 0 -- For garbage collection
);

CREATE TABLE registry_dependencies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  version_id UUID REFERENCES registry_versions(id),
  dependency_type VARCHAR(50), -- runtime, dev, peer, etc.
  dependency_package VARCHAR(500),
  dependency_version VARCHAR(200), -- version constraint
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Protocol Implementations

#### npm Registry (v1 API)

```http
# Package metadata
GET /{scope}/{package}
GET /{scope}/{package}/{version}

# Publish
PUT /{scope}/{package}

# Download tarball
GET /{scope}/{package}/-/{filename}.tgz

# Search
GET /-/v1/search?text={query}

# User/token
PUT /-/user/org.couchdb.user:{username}
POST /-/npm/v1/tokens
```

#### PyPI (PEP 503 Simple API)

```http
# Package index
GET /simple/

# Package versions
GET /simple/{package}/

# Download
GET /packages/{hash}/{filename}

# Upload (Twine compatible)
POST /legacy/
```

#### Docker Registry (OCI Distribution v2)

```http
# Catalog
GET /v2/_catalog

# Tags
GET /v2/{name}/tags/list

# Manifest
GET /v2/{name}/manifests/{reference}
PUT /v2/{name}/manifests/{reference}

# Blobs
GET /v2/{name}/blobs/{digest}
POST /v2/{name}/blobs/uploads/
```

#### apt Repository

```
# Repository structure
/dists/{distribution}/
  Release
  Release.gpg
  InRelease
  main/
    binary-amd64/
      Packages
      Packages.gz
    source/
      Sources
      Sources.gz
      
/pool/main/{prefix}/{package}/
  {package}_{version}_{arch}.deb
```

### Package Publishing Workflow

```yaml
# .github/workflows/publish.yml

name: Publish Package

on:
  release:
    types: [published]

jobs:
  publish-npm:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://code.devflow.dev/registry/npm'
          
      - name: Publish to DevFlow Registry
        run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.DEVFLOW_REGISTRY_TOKEN }}
          
  publish-docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: code.devflow.dev/myorg/myapp:${{ github.ref_name }}
```

### Registry Management API

```http
# Package management
GET    /api/v1/registry/packages
GET    /api/v1/registry/packages/{type}/{namespace}/{name}
DELETE /api/v1/registry/packages/{type}/{namespace}/{name}

# Version management
GET    /api/v1/registry/packages/{id}/versions
DELETE /api/v1/registry/packages/{id}/versions/{version}

# Statistics
GET    /api/v1/registry/packages/{id}/stats
{
  "downloads_total": 15420,
  "downloads_last_30d": 3241,
  "dependents": 47,
  "latest_version": "2.5.1",
  "published_at": "2025-11-15T08:00:00Z"
}

# Storage management
GET /api/v1/registry/storage/stats
POST /api/v1/registry/storage/gc  # Garbage collection
```

---

## Component 5: Project Management ($60k, 3 months)

### Overview

Integrated issue tracking, project boards, and milestone management for project coordination.

### Core Features

**Issues**:
- Issue creation and tracking
- Labels, assignees, milestones
- Issue templates
- Reactions and voting
- Related issues linking
- Due dates

**Project Boards**:
- Kanban-style boards
- Multiple views (board, table, timeline)
- Custom fields
- Automation rules
- Board templates

**Milestones**:
- Milestone creation
- Progress tracking
- Due date management
- Burndown charts

**Integration with DevFlow Hub**:
- Sync issues to Hub workflows
- Auto-create tasks from issues
- Link PRs to workflow phases
- Bi-directional status sync

### Database Schema

```sql
CREATE TABLE issues (
  id BIGSERIAL PRIMARY KEY,
  repo_id BIGINT REFERENCES repository(id),
  number INTEGER,
  title VARCHAR(500),
  body TEXT,
  state VARCHAR(20), -- open, closed
  created_by BIGINT REFERENCES "user"(id),
  assignee_id BIGINT REFERENCES "user"(id),
  milestone_id BIGINT,
  hub_task_id UUID, -- Link to DevFlow Hub task
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  closed_at TIMESTAMP
);

CREATE TABLE issue_labels (
  issue_id BIGINT REFERENCES issues(id),
  label_id BIGINT REFERENCES labels(id),
  PRIMARY KEY (issue_id, label_id)
);

CREATE TABLE project_boards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id BIGINT REFERENCES repository(id),
  org_id BIGINT, -- Organization-level boards
  name VARCHAR(255),
  description TEXT,
  visibility VARCHAR(20),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE board_columns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  board_id UUID REFERENCES project_boards(id),
  name VARCHAR(255),
  position INTEGER,
  automation_rules JSONB
);

CREATE TABLE board_cards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  column_id UUID REFERENCES board_columns(id),
  issue_id BIGINT REFERENCES issues(id),
  pr_id BIGINT REFERENCES pull_request(id),
  position INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Component 6: Security Scanner ($40k, 2 months)

### Overview

Automated security vulnerability detection in code, dependencies, and container images.

### Scanning Types

**Static Application Security Testing (SAST)**:
- Code vulnerability detection
- Hardcoded secrets scanning
- Security anti-patterns
- CWE (Common Weakness Enumeration) checks

**Dependency Scanning**:
- Known CVE detection (via CVE databases)
- Outdated dependency warnings
- License compliance checking
- Supply chain risk assessment

**Container Scanning**:
- Base image vulnerabilities
- Installed package CVEs
- Configuration issues
- Best practice violations

**Secret Detection**:
- API keys and tokens
- Private keys and certificates
- Database credentials
- OAuth tokens

### Integration Points

**Pull Request Checks**:
- Block merge on critical vulnerabilities
- Comment on PRs with findings
- Suggest remediation steps
- Track fix commits

**CI/CD Integration**:
- Pre-commit hooks
- Build-time scanning
- Pre-deployment gates
- Periodic rescanning

**Reporting**:
- Security dashboard
- Vulnerability trends
- Remediation tracking
- Compliance reports

### Tools Integration

**Open Source Tools**:
- **Semgrep**: SAST scanning
- **Trivy**: Container and dependency scanning
- **gitleaks**: Secret detection
- **OSV Scanner**: Vulnerability database

**Database Schema**:

```sql
CREATE TABLE security_scans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id BIGINT REFERENCES repository(id),
  commit_sha VARCHAR(40),
  scan_type VARCHAR(50), -- sast, dependency, container, secrets
  status VARCHAR(20), -- queued, scanning, completed, failed
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE security_findings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scan_id UUID REFERENCES security_scans(id),
  severity VARCHAR(20), -- critical, high, medium, low, info
  category VARCHAR(50), -- cve, cwe, secret, etc.
  title VARCHAR(500),
  description TEXT,
  file_path VARCHAR(1000),
  line_number INTEGER,
  cve_id VARCHAR(50),
  remediation TEXT,
  false_positive BOOLEAN DEFAULT false,
  resolved_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Integration with DevFlow Platform

### DevFlow Hub Integration

**Workflow Triggers**:
- PR creation triggers Hub workflow
- Issue creation creates Hub tasks
- Release triggers deployment workflow
- Security findings update Hub knowledge

**Knowledge Sharing**:
- Code patterns added to Hub knowledge base
- Review feedback informs future reviews
- Security findings update security knowledge
- Build artifacts indexed for search

### DevFlow Runtime Integration

**Automatic Deployment**:
```yaml
# .devflow/deploy.yml

deploy:
  production:
    branch: main
    runtime_app: my-app
    environment: production
    auto_deploy: true
    require_checks: true
    
  staging:
    branch: develop
    runtime_app: my-app-staging
    environment: staging
    auto_deploy: true
```

**Environment Variables**:
- Runtime secrets available in CI/CD
- Database URLs auto-configured
- Service discovery automatic
- Feature flags integration

### DevFlow Analytics Integration

**Metrics Collection**:
- Repository activity
- Build success rates
- Deployment frequency
- Code review metrics
- Package download stats

**Feature Flags**:
- Gradual feature rollout via registry
- A/B test package versions
- Rollback on errors
- Usage analytics per version

---

## API Reference

### Repository API

```http
# List repositories
GET /api/v1/repos
GET /api/v1/orgs/{org}/repos
GET /api/v1/users/{user}/repos

# Repository details
GET /api/v1/repos/{owner}/{repo}
POST /api/v1/orgs/{org}/repos
PATCH /api/v1/repos/{owner}/{repo}
DELETE /api/v1/repos/{owner}/{repo}

# Repository content
GET /api/v1/repos/{owner}/{repo}/contents/{path}
GET /api/v1/repos/{owner}/{repo}/commits
GET /api/v1/repos/{owner}/{repo}/branches
```

### Pull Request API

```http
# List PRs
GET /api/v1/repos/{owner}/{repo}/pulls

# PR details
GET /api/v1/repos/{owner}/{repo}/pulls/{index}
POST /api/v1/repos/{owner}/{repo}/pulls
PATCH /api/v1/repos/{owner}/{repo}/pulls/{index}

# PR reviews
POST /api/v1/repos/{owner}/{repo}/pulls/{index}/reviews
GET /api/v1/repos/{owner}/{repo}/pulls/{index}/reviews

# AI review
POST /api/v1/repos/{owner}/{repo}/pulls/{index}/ai-review
GET /api/v1/repos/{owner}/{repo}/pulls/{index}/ai-review
```

### CI/CD API

```http
# List workflows
GET /api/v1/repos/{owner}/{repo}/workflows

# Trigger workflow
POST /api/v1/repos/{owner}/{repo}/actions/workflows/{id}/dispatches

# Workflow runs
GET /api/v1/repos/{owner}/{repo}/actions/runs
GET /api/v1/repos/{owner}/{repo}/actions/runs/{id}
POST /api/v1/repos/{owner}/{repo}/actions/runs/{id}/cancel

# Artifacts
GET /api/v1/repos/{owner}/{repo}/actions/runs/{id}/artifacts
GET /api/v1/repos/{owner}/{repo}/actions/artifacts/{id}
DELETE /api/v1/repos/{owner}/{repo}/actions/artifacts/{id}
```

### Package Registry API

```http
# Package search
GET /api/v1/registry/search?q={query}&type={type}

# Package info
GET /api/v1/registry/packages/{type}/{namespace}/{name}

# Package versions
GET /api/v1/registry/packages/{id}/versions
GET /api/v1/registry/packages/{id}/versions/{version}

# Package stats
GET /api/v1/registry/packages/{id}/stats
```

---

## Security & Access Control

### Authentication

**Supported Methods**:
- Username/password
- OAuth 2.0 (GitHub, GitLab, Google)
- SAML 2.0 (Enterprise SSO)
- Personal Access Tokens
- SSH keys
- Deploy keys (read-only repo access)

### Authorization

**Repository Permissions**:
- **Owner**: Full control
- **Admin**: Manage settings, can't delete
- **Write**: Push, merge PRs
- **Read**: Clone, view code
- **None**: No access

**Organization Roles**:
- **Owner**: Full org control
- **Member**: Access to org repos based on repo permissions
- **Billing**: Manage billing only

**Team Permissions**:
- Teams group users
- Assign teams to repositories
- Inherit permissions from parent teams

### Package Registry Access

**Visibility Levels**:
- **Public**: Anyone can download
- **Internal**: Authenticated users only
- **Private**: Team/org members only

**Publishing Permissions**:
- Repository write access → can publish
- Registry-specific tokens
- Scoped access per package type

---

## Deployment Architecture

### Components

**Git Server**:
- Load balanced Gitea instances
- Shared PostgreSQL database
- Redis for session caching
- NFS/S3 for Git LFS

**CI/CD Runners**:
- Kubernetes-based auto-scaling
- Docker-in-Docker for builds
- Runner pools per organization
- Resource quotas and limits

**Package Registry**:
- S3/MinIO for blob storage
- PostgreSQL for metadata
- CDN for public packages
- Regional replication

**Security Scanner**:
- Background job workers
- Dedicated scanning cluster
- CVE database sync
- Result caching

### Scaling Considerations

**Git Operations**:
- Read replicas for clone operations
- Pack file caching
- Shallow clone optimization
- Git protocol v2 support

**Build Capacity**:
- Auto-scale runners based on queue
- Priority queues (paid > free)
- Spot instances for cost savings
- Build time limits

**Registry Storage**:
- Deduplication saves ~40% storage
- Lifecycle policies for old versions
- CDN reduces origin load
- Regional caching

---

## Monitoring & Observability

### Metrics

**Repository Metrics**:
- Clone/fetch operations per second
- Push operations per second
- Repository size growth
- Active repositories

**CI/CD Metrics**:
- Build queue length
- Build success/failure rate
- Average build time
- Runner utilization

**Registry Metrics**:
- Package downloads per second
- Storage usage by type
- Publish rate
- Popular packages

**System Metrics**:
- API response times
- Database query performance
- Storage IOPS
- Network bandwidth

### Logging

**Audit Logs**:
- User authentication
- Permission changes
- Repository operations
- Package publishing
- Security events

**Application Logs**:
- HTTP requests
- Git operations
- CI/CD job execution
- Background jobs
- Errors and warnings

### Alerting

**Critical Alerts**:
- API downtime
- Database connection failures
- Storage capacity warnings
- Security incidents
- Build system failures

**Warning Alerts**:
- Slow query performance
- High error rates
- Disk space warnings
- Unusual activity patterns

---

## Migration & Import

### From GitHub

**Import Wizard**:
- OAuth authentication
- Repository selection
- Import options:
  - Code and commits
  - Issues and PRs
  - Releases
  - Wiki
  - Actions workflows
  - Package registry

**Migration Strategy**:
1. Mirror repository to DevFlow Code
2. Verify all data imported
3. Test CI/CD workflows
4. Update package registry clients
5. Redirect users to new location
6. Archive or delete GitHub repo

### From GitLab

**Similar Process**:
- Import via GitLab API
- Convert GitLab CI to Actions
- Migrate GitLab Packages to Universal Registry
- Issue/MR conversion

### From Bitbucket

**Import Support**:
- Bitbucket API integration
- Convert Bitbucket Pipelines
- Issue and PR import
- User mapping

---

## Pricing Strategy

### Self-Hosted (Open Source)

**Free**:
- Unlimited repositories
- Unlimited users
- All core features
- Community support

**Enterprise Add-ons**:
- Advanced security scanning: $10/user/month
- Priority support: $50/user/month
- Custom SLA: Contact sales
- On-premise training: Contact sales

### SaaS (cloud.devflow.dev)

**Free Tier**:
- 5 private repos
- 500 MB package storage
- 2,000 CI/CD minutes/month
- Community support

**Pro ($25/user/month)**:
- Unlimited private repos
- 10 GB package storage
- 10,000 CI/CD minutes/month
- Email support
- Advanced security scanning

**Team ($99/user/month)**:
- Everything in Pro
- 100 GB package storage
- 50,000 CI/CD minutes/month
- SSO/SAML
- Priority support
- SLA 99.9%

**Enterprise (Custom)**:
- Everything in Team
- Unlimited storage
- Unlimited CI/CD minutes
- Dedicated support
- Custom SLA 99.99%
- On-premise option
- Professional services

---

## Success Metrics

### Adoption Metrics

| Metric | Target | Timeline |
|--------|--------|----------|
| Migrated repositories | 100 | Month 6 |
| Migrated repositories | 1,000 | Month 12 |
| Active users | 500 | Month 12 |
| Active users | 5,000 | Month 18 |
| Package types supported | 10 | Month 15 |
| Registry downloads/day | 10,000 | Month 18 |

### Technical Metrics

| Metric | Target |
|--------|--------|
| Git operation latency (p95) | < 500ms |
| CI/CD build start time | < 30 seconds |
| Package download latency | < 100ms |
| API uptime | > 99.9% |
| Build success rate | > 95% |

### Business Metrics

| Metric | Target (Month 18) |
|--------|-------------------|
| Monthly recurring revenue (SaaS) | $50,000 |
| Self-hosted installations | 500 |
| Package registry storage (TB) | 50 |
| CI/CD minutes consumed (millions) | 10 |

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Gitea fork divergence | High | Medium | Automate upstream sync, minimize custom changes |
| Package registry complexity | High | Medium | Phase rollout by package type, extensive testing |
| GitHub Actions compatibility | High | Low | Comprehensive test suite, documentation |
| Storage costs (registry) | Medium | High | Aggressive deduplication, lifecycle policies |
| CI/CD abuse | Medium | Medium | Rate limiting, resource quotas, monitoring |
| Migration friction | Medium | Medium | Import tools, documentation, support |

---

## Open Questions

1. **Gitea Upstream**: Should we contribute AI features back to Gitea or keep proprietary?
   - Recommendation: Open source AI review framework, keep DevFlow Hub integration proprietary

2. **Registry Deduplication**: How aggressive should cross-package-type dedup be?
   - Recommendation: Start conservative (same type only), expand carefully

3. **Build Runners**: Support Windows and macOS runners from day 1?
   - Recommendation: Linux only initially, add Windows/macOS in Month 12-15

4. **Package Signing**: Require package signing for all types?
   - Recommendation: Optional initially, required for critical packages later

---

## Related PRDs

### Core Platform
- [PRD-001: System Overview](./PRD-001-OVERVIEW.md)
- [PRD-007: Secrets Management](./PRD-007-SECRETS-MANAGEMENT.md)
- [PRD-008: Deployment Architecture](./PRD-008-DEPLOYMENT-ARCHITECTURE.md)
- [PRD-009: AOSentry Integration](./PRD-009-AOSENTRY-INTEGRATION.md)

### DevFlow Hub (Integration Points)
- [PRD-002: Knowledge Hub](./PRD-002-KNOWLEDGE-HUB.md) - AI code review knowledge source
- [PRD-003: Workflow Engine](./PRD-003-WORKFLOW-ENGINE.md) - PR triggers workflows
- [PRD-004: MCP Gateway](./PRD-004-MCP-GATEWAY.md) - Agent access to repos
- [PRD-006: Integrations](./PRD-006-INTEGRATIONS.md) - External Git platform sync

### DevFlow Runtime (Integration Points)
- PRD-011: DevFlow Runtime - Automatic deployment target
- PRD-012: DevFlow Analytics - Build and package metrics
- PRD-013: Platform Services - Neo4j dependency graphs

### Developer Tools
- PRD-014: DevFlow CLI - Git and registry operations
- PRD-015: DevFlow Desktop - GUI for Code management

---

## References

### Inspirational Projects
- **Gitea**: https://gitea.io/ - Base Git server
- **GitHub Actions**: https://docs.github.com/en/actions - CI/CD inspiration
- **Verdaccio**: https://verdaccio.org/ - npm registry
- **Harbor**: https://goharbor.io/ - Container registry
- **Artifactory**: https://jfrog.com/artifactory/ - Universal registry

### Standards & Protocols
- **Git Protocol**: https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols
- **OCI Distribution Spec**: https://github.com/opencontainers/distribution-spec
- **npm Registry API**: https://github.com/npm/registry/blob/master/docs/REGISTRY-API.md
- **PyPI Simple API (PEP 503)**: https://peps.python.org/pep-0503/
- **apt Repository Format**: https://wiki.debian.org/DebianRepository/Format

---

**Document Version**: 1.0  
**Status**: Draft - Ready for Review  
**Investment**: $540,000 over 18 months  
**Timeline**: Month 3 (start) → Month 18 (complete)

---

**End of PRD-010**
