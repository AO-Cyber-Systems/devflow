# PRD-005: Unified UI Dashboard

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)

---

## Overview

The Unified UI Dashboard provides a comprehensive web interface for managing knowledge, monitoring workflows, and observing AI agent activities. It serves as the primary control plane for both human users and the command center for understanding what's happening across the DevFlow system.

---

## Goals

### Primary Goals
1. Provide intuitive interface for knowledge management (browse, search, upload, crawl)
2. Enable real-time workflow monitoring and visualization
3. Offer comprehensive observability into agent activities and decisions
4. Support configuration and system administration

### Secondary Goals
1. Enable mobile-responsive design for monitoring on-the-go
2. Support dark/light themes for developer preference
3. Provide exportable reports and analytics
4. Enable collaboration features (comments, sharing)

---

## User Personas

### Developer (Primary User)
- **Needs**: Upload docs, monitor workflows, check agent progress
- **Goals**: Ensure AI agents have proper context, verify work quality
- **Pain Points**: Context switching, unclear agent status, debugging failures

### Team Lead
- **Needs**: Dashboard overview, team metrics, quality insights
- **Goals**: Track productivity, identify bottlenecks, allocate resources
- **Pain Points**: Lack of visibility, no actionable metrics

### System Administrator
- **Needs**: Configure services, manage API keys, monitor health
- **Goals**: Keep system running smoothly, optimize performance
- **Pain Points**: Complex configuration, unclear error messages

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  DevFlow UI Dashboard                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  React Application (TypeScript + Vite)                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Layout & Navigation                      │  │
│  │  - Top Navigation Bar                                 │  │
│  │  - Sidebar Menu                                       │  │
│  │  - Breadcrumbs                                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               View Components                         │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                                                       │  │
│  │  Knowledge Hub View        Workflow View             │  │
│  │  - Source Browser         - Phase Overview           │  │
│  │  - Search Interface       - Task Board (Kanban)      │  │
│  │  - Upload/Crawl UI        - Dependency Graph         │  │
│  │                                                       │  │
│  │  Agent Monitor View        Settings View             │  │
│  │  - Active Agents          - API Keys                 │  │
│  │  - Trajectory Timeline    - Configuration            │  │
│  │  - Guardian Alerts        - System Health            │  │
│  │                                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            State Management (Zustand)                 │  │
│  │  - Knowledge State                                    │  │
│  │  - Workflow State                                     │  │
│  │  - Agent State                                        │  │
│  │  - UI State                                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           API Clients & WebSocket                     │  │
│  │  - REST API Client (React Query)                      │  │
│  │  - WebSocket Client (Socket.IO)                       │  │
│  │  - Real-time Updates                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │Knowledge│      │Workflow │      │   MCP   │
   │   Hub   │      │ Engine  │      │ Gateway │
   └─────────┘      └─────────┘      └─────────┘
```

---

## Deployment Modes

DevFlow UI supports two distinct deployment modes:

### 1. Local UI (Lightweight)
**Focus**: Single-user development experience.
- **Host**: Docker container on localhost (e.g., `http://localhost:3000`)
- **Auth**: Minimal/None (single user)
- **Connection**: Direct connection to local services (Qdrant, Postgres)
- **Performance**: Low resource footprint (<100MB RAM)

### 2. Hosted UI (SaaS/Enterprise)
**Focus**: Multi-user collaboration and management.
- **Host**: Kubernetes cluster (e.g., `https://app.devflow.dev`)
- **Auth**: Full OAuth/SAML via Supabase Auth
- **Connection**: Via secure API Gateway
- **Features**: Multi-tenancy, team management, billing, audit logs

---

## Core Views

### 1. Dashboard (Home)
**Purpose**: Overview of system status and recent activity.
```
┌────────────────────────────────────────────────────────────┐
│ DevFlow Dashboard                                  🔍 ⚙️ 👤│
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ Knowledge   │  │ Active      │  │ Agents      │      │
│  │ Sources     │  │ Workflows   │  │ Running     │      │
│  │             │  │             │  │             │      │
│  │    42       │  │     3       │  │     7       │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                            │
│  Recent Activity                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 🕐 2m ago  Agent-A completed "Implement auth"     │    │
│  │ 🕐 5m ago  New knowledge source: "API Docs"       │    │
│  │ 🕐 8m ago  Guardian intervened: Agent-B           │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  Workflow Status                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Auth Implementation    [████████████░░] 85%       │    │
│  │ Frontend Redesign      [████░░░░░░░░░░] 30%       │    │
│  │ API Optimization       [████████████░░] 90%       │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Components**:
- Metric cards (sources, workflows, agents)
- Activity feed (real-time updates via WebSocket)
- Workflow progress bars
- Quick actions (add source, start workflow)
- Integration status indicators (Jira, Confluence, GitHub - see PRD-006)

### 2. Knowledge Hub View

**Purpose**: Manage and search project knowledge.

**Layout**:
```
┌────────────────────────────────────────────────────────────┐
│ Knowledge Hub              [+ Add Source ▼] 🔍 Search      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Sources (42)                                              │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Filter: [All] [Web] [Docs] [Code]                │    │
│  │ Tags: [documentation] [api] [security]            │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ┌────────────────────────────────────────────┐           │
│  │ 📄 Framework Documentation                  │           │
│  │    https://docs.example.com                │           │
│  │    342 chunks | Last updated 2 hours ago   │           │
│  │    Tags: documentation, framework          │           │
│  │    [View] [Update] [Delete]                │           │
│  ├────────────────────────────────────────────┤           │
│  │ 📑 Architecture Decision Record             │           │
│  │    Uploaded PDF | 42 chunks                │           │
│  │    Tags: architecture, adr                 │           │
│  │    [View] [Delete]                         │           │
│  └────────────────────────────────────────────┘           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Features**:

**A. Add Source Modal**
```
┌─────────────────────────────────────┐
│ Add Knowledge Source                │
├─────────────────────────────────────┤
│                                     │
│  Source Type:                       │
│  ○ Web Crawl                        │
│  ○ Upload Document                  │
│  ○ Manual Entry                     │
│                                     │
│  [Continue]                         │
│                                     │
└─────────────────────────────────────┘
```

**B. Web Crawl Configuration**
```
┌─────────────────────────────────────┐
│ Crawl Website                       │
├─────────────────────────────────────┤
│                                     │
│  URL: [https://docs.example.com  ] │
│                                     │
│  Max Depth: [3]                     │
│  Max Pages: [1000]                  │
│                                     │
│  Tags: [documentation] [api]        │
│                                     │
│  [Start Crawl]                      │
│                                     │
└─────────────────────────────────────┘
```

**C. Search Interface**
```
┌─────────────────────────────────────────────────┐
│ 🔍 Search Knowledge Base                        │
├─────────────────────────────────────────────────┤
│                                                 │
│  [How to implement JWT authentication?]         │
│                                                 │
│  Mode: ◉ Hybrid  ○ Semantic  ○ Reranked        │
│  Filters: Tags [authentication] [security]      │
│                                                 │
│  [Search]                                       │
│                                                 │
└─────────────────────────────────────────────────┘

Results (47 found in 123ms)

┌─────────────────────────────────────────────────┐
│ 📄 Authentication Documentation                 │
│    Score: 0.89                                  │
│                                                 │
│    To implement JWT authentication, first...    │
│    [Read More] [View Source]                    │
│                                                 │
│    Code Example (Python):                       │
│    ```python                                    │
│    def authenticate(user, password):            │
│        # Generate JWT token                     │
│    ```                                          │
└─────────────────────────────────────────────────┘
```

### 3. Workflow View

**Purpose**: Monitor and manage active workflows.

**Layout**:
```
┌────────────────────────────────────────────────────────────┐
│ Workflows                              [+ New Workflow]     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Auth Implementation Workflow                              │
│  Status: In Progress | Started: 2h ago | Progress: 85%    │
│                                                            │
│  Phases                                                    │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Phase 1: Analysis          [✓] 3 tasks done      │    │
│  │ Phase 2: Implementation    [⚙] 5 in progress     │    │
│  │ Phase 3: Validation        [○] 2 pending         │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  Kanban Board                                              │
│  ┌─────┬─────┬──────────┬────────┬──────┐               │
│  │Back │Ready│In Progres│Review  │Done  │               │
│  │log  │     │s         │        │      │               │
│  ├─────┼─────┼──────────┼────────┼──────┤               │
│  │TASK │TASK │TASK-005  │TASK-007│TASK-9│               │
│  │-001 │-003 │Phase 2   │Phase 3 │✓     │               │
│  │     │     │Agent-A   │Agent-B │      │               │
│  └─────┴─────┴──────────┴────────┴──────┘               │
│                                                            │
│  Dependency Graph                    [View Full Graph]     │
│  ┌──────────────────────────────────────────────────┐    │
│  │     TASK-001                                      │    │
│  │         ↓                                         │    │
│  │    ┌────┴────┐                                    │    │
│  │    ↓         ↓                                    │    │
│  │ TASK-002  TASK-003                               │    │
│  │    ↓         ↓                                    │    │
│  │    └────┬────┘                                    │    │
│  │         ↓                                         │    │
│  │     TASK-004                                      │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Interactive Features**:
- Drag-and-drop on Kanban board
- Click task to see details
- Click agent to see trajectory
- Expand graph for full visualization

### 4. Agent Monitor View

**Purpose**: Real-time agent observability.

**Layout**:
```
┌────────────────────────────────────────────────────────────┐
│ Agent Monitor                           7 agents active     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Agent-A                    Phase 2 | Task-005     │    │
│  │ Coherence: 0.89 🟢        Active: 15 minutes      │    │
│  │                                                    │    │
│  │ Current Action:                                    │    │
│  │ "Writing authentication logic in auth.py"          │    │
│  │                                                    │    │
│  │ Recent Trajectory:                                 │    │
│  │ 🕐 14:30 Created auth.py file                      │    │
│  │ 🕐 14:32 Searched knowledge: "JWT best practices" │    │
│  │ 🕐 14:35 Implemented token generation             │    │
│  │ 🕐 14:38 Writing tests for auth endpoints         │    │
│  │                                                    │    │
│  │ [View Full Session] [Send Message]                │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Agent-B                    Phase 3 | Task-007     │    │
│  │ Coherence: 0.45 🟡        Active: 8 minutes       │    │
│  │                                                    │    │
│  │ ⚠️ Guardian Alert:                                │    │
│  │ "Agent drifting from Phase 3 validation goals"    │    │
│  │ Intervention sent 2 minutes ago                    │    │
│  │                                                    │    │
│  │ [View Details] [Manual Intervention]              │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Real-time Updates**:
- WebSocket connection for live trajectory updates
- Color-coded coherence scores
- Guardian alerts and interventions
- Agent status changes

### 6. DevFlow Code View
**Purpose**: Manage repositories, pull requests, and packages.

**Layout**:
```
┌────────────────────────────────────────────────────────────┐
│ DevFlow Code                                [+ New Repo]    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Repositories                                              │
│  ┌──────────────────────────────────────────────────┐    │
│  │ my-app                Updated 2m ago            │    │
│  │ ● JavaScript   ★ 12   ⑂ 3                       │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  Pull Requests                                             │
│  ┌──────────────────────────────────────────────────┐    │
│  │ #42 Add login page    [Review Required]          │    │
│  │ opened by @alice      [CI: Passing]              │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  CI/CD Pipelines                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Deploy to Staging     🟢 Success (2m ago)       │    │
│  │ Run Tests             🔴 Failed (15m ago)       │    │
│  └──────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
```

### 7. DevFlow Runtime View
**Purpose**: Manage deployments, services, and analytics.

**Layout**:
```
┌────────────────────────────────────────────────────────────┐
│ DevFlow Runtime                           [prod] ▼          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Services                                                  │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Database (Postgres)   🟢 Healthy                │    │
│  │ Auth Service          🟢 Healthy                │    │
│  │ Storage               🟢 Healthy                │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  Deployments                                               │
│  ┌──────────────────────────────────────────────────┐    │
│  │ v1.2.3 (main)         🚀 Active                 │    │
│  │ v1.2.2 (main)         ⏸️ Inactive               │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  Analytics (Feature Flags)                                 │
│  ┌──────────────────────────────────────────────────┐    │
│  │ new-onboarding        🟢 Enabled (50%)          │    │
│  │ beta-search           🔴 Disabled               │    │
│  └──────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
```

### 8. Settings View
**Purpose**: System configuration and administration.
```
┌────────────────────────────────────────────────────────────┐
│ Settings                                                   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─ API Keys ──────────────────────────────────────┐     │
│  │                                                  │     │
│  │  OpenAI API Key:  [sk-...] ✓                   │     │
│  │  Anthropic Key:   [sk-...] ✓                   │     │
│  │  OpenRouter Key:  [Not Set] ✗                  │     │
│  │                                                  │     │
│  │  [Add New Key]                                  │     │
│  └──────────────────────────────────────────────────┘     │
│                                                            │
│  ┌─ LLM Configuration ─────────────────────────────┐     │
│  │                                                  │     │
│  │  Default Provider:    [OpenAI ▼]               │     │
│  │  Default Model:       [gpt-4 ▼]                │     │
│  │  Embedding Model:     [text-embedding-3-large] │     │
│  │                                                  │     │
│  │  Agent CLI Tool:      [Claude Code ▼]          │     │
│  │  Agent Model:         [sonnet ▼]               │     │
│  │                                                  │     │
│  │  [Save Changes]                                 │     │
│  └──────────────────────────────────────────────────┘     │
│                                                            │
│  ┌─ Integrations (see PRD-006) ────────────────────┐     │
│  │                                                  │     │
│  │  Atlassian:       🟢 Connected (OAuth)         │     │
│  │    - Jira:        PROJ, DEV (2 projects)       │     │
│  │    - Confluence:  DEV space                    │     │
│  │                                                  │     │
│  │  GitHub:          🟢 Connected (OAuth)         │     │
│  │    - Repo:        myorg/myrepo                 │     │
│  │    - Projects:    3 active                     │     │
│  │                                                  │     │
│  │  [Connect Atlassian] [Connect GitHub]          │     │
│  │  [Manage Integrations]                         │     │
│  └──────────────────────────────────────────────────┘     │
│                                                            │
│  ┌─ System Health ─────────────────────────────────┐     │
│  │                                                  │     │
│  │  Knowledge Hub:    🟢 Running                   │     │
│  │  Workflow Engine:  🟢 Running                   │     │
│  │  MCP Gateway:      🟢 Running                   │     │
│  │  Qdrant:          🟢 Connected                 │     │
│  │  Database:        🟢 Connected                 │     │
│  │                                                  │     │
│  │  [View Logs] [Restart Services]                │     │
│  └──────────────────────────────────────────────────┘     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Integration Management** (see PRD-006 for details):
- OAuth connection setup for Atlassian and GitHub
- Configure space/project mappings
- View sync status and resolve conflicts
- Manage webhook registrations

---

## Component Library

### Design System

**Colors** (Tailwind CSS):
- Primary: Blue (600)
- Success: Green (500)
- Warning: Yellow (500)
- Error: Red (500)
- Neutral: Gray (500-900)

**Typography**:
- Headings: Inter (font-semibold)
- Body: Inter (font-normal)
- Code: Fira Code (font-mono)

**Spacing**:
- Base unit: 4px (Tailwind's default)
- Component padding: 4 (16px)
- Section margins: 6 (24px)

### Reusable Components

#### MetricCard
```tsx
interface MetricCardProps {
  title: string;
  value: number | string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
}

function MetricCard({ title, value, icon, trend }: MetricCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-500 text-sm">{title}</p>
          <p className="text-3xl font-semibold mt-1">{value}</p>
        </div>
        {icon && <div className="text-blue-500">{icon}</div>}
      </div>
      {trend && (
        <div className="mt-4 flex items-center text-sm">
          <span className={trend.direction === 'up' ? 'text-green-500' : 'text-red-500'}>
            {trend.direction === 'up' ? '↑' : '↓'} {trend.value}%
          </span>
          <span className="text-gray-500 ml-2">vs last week</span>
        </div>
      )}
    </div>
  );
}
```

#### TaskCard
```tsx
interface TaskCardProps {
  task: Task;
  onView: () => void;
  onUpdate: (status: string) => void;
}

function TaskCard({ task, onView, onUpdate }: TaskCardProps) {
  return (
    <div className="bg-white rounded-lg border p-4 hover:shadow-md transition">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500">
              {task.id}
            </span>
            <PhaseBadge phase={task.phase_id} />
            <PriorityBadge priority={task.priority} />
          </div>
          <p className="mt-2 text-sm line-clamp-2">{task.description}</p>
        </div>
      </div>
      
      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          {task.assigned_agent_id && (
            <span>👤 {task.assigned_agent_id}</span>
          )}
          <span>🕐 {formatRelativeTime(task.created_at)}</span>
        </div>
        
        <div className="flex gap-2">
          <button onClick={onView} className="text-blue-600 hover:text-blue-800">
            View
          </button>
        </div>
      </div>
    </div>
  );
}
```

#### KanbanColumn
```tsx
interface KanbanColumnProps {
  title: string;
  tasks: Task[];
  onDrop: (task: Task) => void;
}

function KanbanColumn({ title, tasks, onDrop }: KanbanColumnProps) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 min-w-[300px]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">{title}</h3>
        <span className="text-sm text-gray-500">{tasks.length}</span>
      </div>
      
      <div 
        className="space-y-3"
        onDrop={(e) => handleDrop(e, onDrop)}
        onDragOver={(e) => e.preventDefault()}
      >
        {tasks.map(task => (
          <TaskCard
            key={task.id}
            task={task}
            draggable
            onDragStart={(e) => e.dataTransfer.setData('task', task.id)}
          />
        ))}
      </div>
    </div>
  );
}
```

---

## State Management

### Zustand Stores

```typescript
// Knowledge Store
interface KnowledgeState {
  sources: KnowledgeSource[];
  selectedSource: KnowledgeSource | null;
  isLoading: boolean;
  
  fetchSources: () => Promise<void>;
  addSource: (source: KnowledgeSource) => Promise<void>;
  deleteSource: (id: string) => Promise<void>;
  searchKnowledge: (query: string) => Promise<SearchResult>;
}

const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  sources: [],
  selectedSource: null,
  isLoading: false,
  
  fetchSources: async () => {
    set({ isLoading: true });
    const sources = await api.getKnowledgeSources();
    set({ sources, isLoading: false });
  },
  
  // ... other methods
}));

// Workflow Store
interface WorkflowState {
  workflows: Workflow[];
  activeWorkflow: Workflow | null;
  tasks: Task[];
  kanbanColumns: KanbanColumns;
  
  fetchWorkflows: () => Promise<void>;
  claimTask: (phaseId: number) => Promise<Task>;
  updateTaskStatus: (id: string, status: string) => Promise<void>;
}

// Agent Store
interface AgentState {
  agents: Agent[];
  trajectories: Map<string, Trajectory[]>;
  
  fetchAgents: () => Promise<void>;
  subscribeToTrajectory: (agentId: string) => void;
}
```

### React Query

```typescript
// Knowledge queries
const useKnowledgeSources = () => {
  return useQuery({
    queryKey: ['knowledge', 'sources'],
    queryFn: () => api.getKnowledgeSources(),
    refetchInterval: 30000, // Refresh every 30s
  });
};

const useSearchKnowledge = (query: string) => {
  return useQuery({
    queryKey: ['knowledge', 'search', query],
    queryFn: () => api.searchKnowledge(query),
    enabled: query.length > 0,
  });
};

// Workflow queries
const useWorkflows = () => {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: () => api.getWorkflows(),
    refetchInterval: 10000, // Refresh every 10s
  });
};

const useKanbanBoard = () => {
  return useQuery({
    queryKey: ['kanban'],
    queryFn: () => api.getKanbanBoard(),
    refetchInterval: 5000, // Refresh every 5s
  });
};

// Mutations
const useCreateTask = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (task: CreateTaskInput) => api.createTask(task),
    onSuccess: () => {
      // Invalidate kanban board query to refetch
      queryClient.invalidateQueries(['kanban']);
    },
  });
};
```

---

## Real-time Updates

### WebSocket Integration

```typescript
import io from 'socket.io-client';

class WebSocketService {
  private socket: Socket;
  
  constructor() {
    this.socket = io('http://localhost:8181', {
      transports: ['websocket'],
    });
    
    this.setupListeners();
  }
  
  private setupListeners() {
    // Task updates
    this.socket.on('task_created', (task: Task) => {
      console.log('New task:', task);
      // Update UI
    });
    
    this.socket.on('task_updated', (task: Task) => {
      console.log('Task updated:', task);
      // Update UI
    });
    
    // Agent updates
    this.socket.on('agent_trajectory', (data: { agent_id: string, action: string }) => {
      console.log('Agent action:', data);
      // Update agent view
    });
    
    this.socket.on('guardian_intervention', (data: GuardianIntervention) => {
      console.log('Guardian alert:', data);
      // Show notification
    });
    
    // Knowledge updates
    this.socket.on('crawl_progress', (data: { source_id: string, progress: number }) => {
      console.log('Crawl progress:', data);
      // Update progress bar
    });
  }
  
  subscribeToAgent(agentId: string) {
    this.socket.emit('subscribe_agent', agentId);
  }
  
  unsubscribeFromAgent(agentId: string) {
    this.socket.emit('unsubscribe_agent', agentId);
  }
}

export const wsService = new WebSocketService();
```

---

## Responsive Design

### Breakpoints
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

### Mobile Adaptations
- Stack columns vertically
- Collapsible sidebar
- Bottom navigation bar
- Swipeable Kanban columns
- Simplified graphs (tap to expand)

---

## Testing Strategy

### Unit Tests (Vitest + React Testing Library)

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { TaskCard } from './TaskCard';

describe('TaskCard', () => {
  const mockTask = {
    id: 'task-123',
    description: 'Implement authentication',
    phase_id: 2,
    status: 'in_progress',
    priority: 'high',
  };
  
  it('renders task information', () => {
    render(<TaskCard task={mockTask} onView={() => {}} onUpdate={() => {}} />);
    
    expect(screen.getByText('task-123')).toBeInTheDocument();
    expect(screen.getByText(/Implement authentication/)).toBeInTheDocument();
  });
  
  it('calls onView when View button clicked', () => {
    const onView = vi.fn();
    render(<TaskCard task={mockTask} onView={onView} onUpdate={() => {}} />);
    
    fireEvent.click(screen.getByText('View'));
    expect(onView).toHaveBeenCalled();
  });
});
```

### Integration Tests

```typescript
import { renderWithProviders } from './test-utils';
import { KnowledgeView } from './KnowledgeView';

describe('KnowledgeView', () => {
  it('displays knowledge sources', async () => {
    const { findByText } = renderWithProviders(<KnowledgeView />);
    
    expect(await findByText('Framework Documentation')).toBeInTheDocument();
  });
  
  it('allows searching knowledge', async () => {
    const { getByPlaceholderText, findByText } = renderWithProviders(<KnowledgeView />);
    
    const searchInput = getByPlaceholderText('Search knowledge...');
    fireEvent.change(searchInput, { target: { value: 'authentication' } });
    
    expect(await findByText(/JWT authentication/)).toBeInTheDocument();
  });
});
```

### E2E Tests (Playwright)

```typescript
import { test, expect } from '@playwright/test';

test('complete workflow: create task and monitor', async ({ page }) => {
  // Navigate to workflows
  await page.goto('http://localhost:3737/workflows');
  
  // Create new task
  await page.click('text=New Task');
  await page.fill('[placeholder="Task description"]', 'Test task');
  await page.selectOption('[name="phase"]', '2');
  await page.click('text=Create');
  
  // Verify task appears in Kanban
  await expect(page.locator('text=Test task')).toBeVisible();
  
  // Navigate to agent monitor
  await page.click('text=Agents');
  
  // Wait for agent to pick up task
  await expect(page.locator('text=Test task')).toBeVisible({ timeout: 10000 });
});
```

---

## Performance Optimization

### Code Splitting

```typescript
// Lazy load views
const KnowledgeView = lazy(() => import('./views/KnowledgeView'));
const WorkflowView = lazy(() => import('./views/WorkflowView'));
const AgentMonitorView = lazy(() => import('./views/AgentMonitorView'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/knowledge" element={<KnowledgeView />} />
        <Route path="/workflows" element={<WorkflowView />} />
        <Route path="/agents" element={<AgentMonitorView />} />
      </Routes>
    </Suspense>
  );
}
```

### Virtual Scrolling

```typescript
import { FixedSizeList } from 'react-window';

function TaskList({ tasks }: { tasks: Task[] }) {
  return (
    <FixedSizeList
      height={600}
      itemCount={tasks.length}
      itemSize={100}
      width="100%"
    >
      {({ index, style }) => (
        <div style={style}>
          <TaskCard task={tasks[index]} />
        </div>
      )}
    </FixedSizeList>
  );
}
```

### Memoization

```typescript
const MemoizedTaskCard = memo(TaskCard, (prev, next) => {
  return prev.task.id === next.task.id && 
         prev.task.status === next.task.status;
});
```

---

## Accessibility

### ARIA Labels

```tsx
<button
  aria-label="Create new task"
  aria-describedby="create-task-help"
  onClick={handleCreate}
>
  + New Task
</button>
```

### Keyboard Navigation

```tsx
function TaskCard({ task }: TaskCardProps) {
  const handleKeyPress = (e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      onView();
    }
  };
  
  return (
    <div
      tabIndex={0}
      onKeyPress={handleKeyPress}
      role="button"
      aria-label={`Task ${task.id}: ${task.description}`}
    >
      {/* ... */}
    </div>
  );
}
```

---

## Success Metrics

### Performance
- First Contentful Paint: < 1.5s
- Time to Interactive: < 3s
- Largest Contentful Paint: < 2.5s

### Usability
- Task Time (create task): < 30 seconds
- Error Rate: < 2%
- User Satisfaction: > 4/5

### Engagement
- Daily Active Users: > 80% of total users
- Session Duration: > 15 minutes
- Feature Adoption: > 70% use all core features

---

## Integration Dashboard View (PRD-006)

**Purpose**: Manage external system integrations and resolve sync conflicts.

**Key Features**:
- OAuth connection management (Atlassian, GitHub)
- Sync status monitoring across all platforms
- Conflict resolution interface (see PRD-006 Section on Conflict Resolution)
- Webhook health monitoring
- Integration analytics (sync success rates, latency)

**Example Conflict Resolution UI**:
```
┌─────────────────────────────────────────────────────────────┐
│ Sync Conflicts                                    [3 Pending]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ⚠️ Hierarchy Violation - Jira Story PROJ-123              │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ Story "Implement login" has no Epic parent           │ │
│ │                                                       │ │
│ │ Recommended: Link to Epic                            │ │
│ │ ○ Link to PROJ-100: "User Auth Epic"                │ │
│ │ ○ Link to PROJ-50: "Mobile App Epic"                │ │
│ │ ○ Create new Epic in DevFlow                        │ │
│ │ ○ Keep in Jira only (don't sync)                    │ │
│ │                                                       │ │
│ │ [Resolve Conflict]          [Ignore]                 │ │
│ └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

For complete integration UI specifications, see **PRD-006: SDLC Tool Integrations**.

---

## Future Enhancements

1. **Mobile App**: Native iOS/Android companion app
2. **Collaboration**: Real-time collaborative editing
3. **Notifications**: Push notifications for important events
4. **Customization**: User-configurable dashboards
5. **Analytics Dashboard**: Advanced metrics and insights
6. **Export/Import**: Workflow and knowledge export/import
7. **API Playground**: Interactive API testing interface
8. **Integration Templates**: Pre-configured integration setups (see PRD-006)

---

**End of PRD-005**
