# PRD-003: Adaptive Workflow Engine

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)

---

## Overview

The Adaptive Workflow Engine is DevFlow's orchestration layer that enables AI agents to dynamically create and execute tasks based on real-time discoveries. Unlike traditional workflow systems with rigid, pre-defined task sequences, this engine uses a semi-structured approach where phases define *what kind of work* should happen, but agents determine the *specific tasks* needed based on what they discover.

---

## Core Concept: Semi-Structured Workflows

### The Problem with Fully Structured Workflows

Traditional agentic frameworks require:
```python
# Traditional approach - RIGID
tasks = [
    Task("Analyze requirements", prompt="Read PRD and..."),
    Task("Design architecture", prompt="Create a design for..."),
    Task("Implement feature X", prompt="Write code to..."),
    # Must predefine EVERY scenario
]
```

**Limitations:**
- Must anticipate every possible scenario upfront
- Cannot adapt when agents discover new requirements
- Breaks when reality diverges from predictions
- No way to handle emergent complexity

### The DevFlow Approach: Phase-Based Discovery

Instead, we define *phase types* and let agents create specific tasks:

```python
# DevFlow approach - ADAPTIVE
phases = [
    Phase(
        id=1,
        name="analysis",
        description="Understand requirements and plan approach",
        # Agents working in this phase can create tasks like:
        # - "Analyze authentication requirements"
        # - "Research OAuth providers"
        # - "Investigate existing patterns"
    ),
    Phase(
        id=2,
        name="implementation",
        description="Build features and fix issues",
        # Agents create implementation tasks based on discoveries:
        # - "Implement JWT auth"
        # - "Add rate limiting"
        # - "Optimize caching pattern"
    ),
    Phase(
        id=3,
        name="validation",
        description="Test and verify work",
        # Agents create validation tasks based on what was built:
        # - "Test auth endpoints"
        # - "Verify rate limiting"
        # - "Benchmark performance"
    )
]
```

**Key Insight**: Phases provide structure (work types), but agents write task descriptions dynamically based on actual discoveries.

---

## Goals

### Primary Goals
1. Enable agents to spawn new tasks in any phase based on discoveries
2. Prevent chaos through Kanban coordination and blocking relationships
3. Ensure agents stay aligned with phase goals via Guardian monitoring
4. Support parallel execution with proper dependency management

### Secondary Goals
1. Provide workflow observability and decision tracking
2. Enable workflow templates for common patterns
3. Support human-in-the-loop intervention when needed
4. Maintain complete workflow history for learning

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           Adaptive Workflow Engine                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────┐     ┌────────────────┐                │
│  │  Phase Manager │     │ Task Spawner   │                │
│  │                │     │                │                │
│  │ - Define phases│◄───►│ - Create tasks │                │
│  │ - Assign agents│     │ - Set priority │                │
│  │ - Track status │     │ - Link deps    │                │
│  └────────────────┘     └────────────────┘                │
│                                                             │
│  ┌────────────────┐     ┌────────────────┐                │
│  │ Kanban Board   │     │   Guardian     │                │
│  │                │     │   Monitor      │                │
│  │ - Track work   │     │                │                │
│  │ - Dependencies │     │ - Watch agents │                │
│  │ - Status flow  │     │ - Detect drift │                │
│  │ - Blocking     │     │ - Intervene    │                │
│  └────────────────┘     └────────────────┘                │
│                                                             │
│  ┌────────────────┐     ┌────────────────┐                │
│  │ Agent Runtime  │     │  Workflow      │                │
│  │                │     │  Visualizer    │                │
│  │ - Spawn agents │     │                │                │
│  │ - tmux/worktree│     │ - Task graph   │                │
│  │ - Isolation    │     │ - Phase view   │                │
│  └────────────────┘     └────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Phase System

**Definition**: A phase is a logical grouping of work types with clear entry/exit criteria.

```python
@dataclass
class Phase:
    """Defines a type of work that can be performed."""
    
    id: int
    name: str
    description: str
    
    # MANDATORY: What must be done for tasks in this phase
    done_definitions: List[str]
    
    # Guide agents on HOW to work in this phase
    additional_notes: str
    
    # Where agents work (project directory)
    working_directory: str
    
    # Optional: Validation rules
    validation_criteria: Optional[List[str]] = None
    
    # Optional: Phase-specific tools
    allowed_tools: Optional[List[str]] = None
```

**Example Phase Definition**:

```python
PHASE_ANALYSIS = Phase(
    id=1,
    name="requirement_analysis",
    description="Understand requirements and identify components",
    done_definitions=[
        "All requirements documented",
        "Components identified and listed",
        "Dependencies mapped",
        "Phase 2 implementation tasks created for each component",
        "Task marked as done"
    ],
    additional_notes="""
    🎯 YOUR MISSION: Break down requirements into buildable components
    
    MANDATORY STEPS:
    1. Read the project requirements (PRD, user stories, specs)
    2. Identify major components needed
    3. For EACH component, create a Phase 2 implementation task
    4. Mark your task as done
    
    ✅ GOOD OUTPUT:
    - "Identified 5 components: Auth, API, Frontend, DB, Workers"
    - "Created Phase 2 tasks: TASK-001 (Auth), TASK-002 (API)..."
    - "Documented dependencies: Frontend depends on API"
    
    ❌ BAD OUTPUT:
    - "I think we need an API" (no concrete task creation)
    - Starting to code (wrong phase!)
    - Creating a Phase 1 task (should be Phase 2)
    """,
    working_directory=".",
    validation_criteria=[
        "At least one Phase 2 task created",
        "All components documented",
        "Dependencies specified"
    ]
)
```

### 2. Task System

**Definition**: A task is a specific piece of work created dynamically by agents.

```python
@dataclass
class Task:
    """A specific piece of work to be done."""
    
    id: str
    description: str  # Agent-written, based on discovery
    phase_id: int
    status: TaskStatus  # pending, in_progress, done, failed
    priority: Priority  # high, medium, low
    
    # Agent assignment
    assigned_agent_id: Optional[str] = None
    
    # Coordination
    blocks: List[str] = []  # Task IDs this task blocks
    blocked_by: List[str] = []  # Task IDs blocking this task
    
    # Tracking
    created_by: str  # Which agent created this task
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Context
    parent_task_id: Optional[str] = None
    child_task_ids: List[str] = []
    
    # Metadata
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
```

**Task Creation Flow**:

```python
# Agent discovers need for authentication
# Agent is working in Phase 1 (analysis)

# Agent uses MCP tool to create a Phase 2 task:
task = create_task(
    description="""
    Phase 2: Implement JWT Authentication
    
    Requirements discovered:
    - Need JWT tokens for API access
    - Tokens expire in 1 hour
    - Refresh token mechanism needed
    - Store tokens in Redis
    
    Acceptance criteria:
    - /auth/login endpoint returns JWT
    - /auth/refresh endpoint returns new JWT
    - All API endpoints validate JWT
    - Tests cover happy path and errors
    """,
    phase_id=2,  # Implementation phase
    priority="high",
    blocked_by=[],  # Can start immediately
    tags=["authentication", "security"]
)

# This task will be picked up by a Phase 2 agent
```

### 3. Kanban Board

**Purpose**: Coordinate work across multiple agents, prevent duplication, track dependencies.

**Board Columns**:
```
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│ Backlog  │  Ready   │In Progress│ Review  │   Done   │
├──────────┼──────────┼──────────┼──────────┼──────────┤
│          │          │          │          │          │
│ TASK-001 │ TASK-003 │ TASK-005 │ TASK-007 │ TASK-009 │
│ Phase 1  │ Phase 2  │ Phase 2  │ Phase 3  │ Phase 1  │
│          │          │ Agent-A  │ Agent-B  │ ✓        │
│          │          │          │          │          │
│ TASK-002 │ TASK-004 │ TASK-006 │          │ TASK-010 │
│ Phase 1  │ Phase 2  │ Phase 3  │          │ Phase 2  │
│ Blocked  │          │ Agent-C  │          │ ✓        │
│          │          │          │          │          │
└──────────┴──────────┴──────────┴──────────┴──────────┘
```

**Blocking Rules**:
```python
class BlockingRule:
    """Define when tasks can move to Ready."""
    
    def can_start(self, task: Task, board: KanbanBoard) -> bool:
        """Check if task can move from Backlog to Ready."""
        
        # All blocking tasks must be done
        for blocking_id in task.blocked_by:
            blocking_task = board.get_task(blocking_id)
            if blocking_task.status != TaskStatus.DONE:
                return False
        
        # Phase dependencies (e.g., Phase 2 can't start before Phase 1 has results)
        if task.phase_id == 2:
            # Need at least one Phase 1 task done
            phase1_tasks = board.get_tasks_by_phase(1)
            if not any(t.status == TaskStatus.DONE for t in phase1_tasks):
                return False
        
        return True
```

**Implementation**:
```python
class KanbanBoard:
    """Manages task coordination."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.columns = {
            "backlog": [],
            "ready": [],
            "in_progress": [],
            "review": [],
            "done": []
        }
    
    def create_task(self, task: Task) -> str:
        """Add new task to backlog."""
        self.tasks[task.id] = task
        self.columns["backlog"].append(task.id)
        self._update_ready_queue()
        return task.id
    
    def claim_task(self, agent_id: str, phase_id: int) -> Optional[Task]:
        """Agent claims next available task for their phase."""
        for task_id in self.columns["ready"]:
            task = self.tasks[task_id]
            if task.phase_id == phase_id and not task.assigned_agent_id:
                task.assigned_agent_id = agent_id
                task.status = TaskStatus.IN_PROGRESS
                self._move_task(task_id, "ready", "in_progress")
                return task
        return None
    
    def complete_task(self, task_id: str):
        """Mark task as done, unblock dependent tasks."""
        task = self.tasks[task_id]
        task.status = TaskStatus.DONE
        task.completed_at = datetime.now()
        self._move_task(task_id, "in_progress", "done")
        self._update_ready_queue()
    
    def _update_ready_queue(self):
        """Move unblocked tasks from backlog to ready."""
        for task_id in list(self.columns["backlog"]):
            task = self.tasks[task_id]
            if self._can_start(task):
                self._move_task(task_id, "backlog", "ready")
```

### 4. Guardian Monitor

**Purpose**: Ensure agents stay aligned with phase goals and follow mandatory steps.

**Monitoring Strategy**:

```python
class GuardianMonitor:
    """Watches agents and intervenes when they drift."""
    
    def __init__(self, interval_seconds: int = 60):
        self.interval = interval_seconds
        self.coherence_threshold = 0.7  # 70% alignment required
        self.llm_client = AOSentryClient()  # Unified LLM gateway
    
    async def monitor_agents(self):
        """Continuously monitor all active agents."""
        while True:
            active_agents = self.get_active_agents()
            
            for agent in active_agents:
                trajectory = self.get_agent_trajectory(agent.id)
                task = self.get_agent_task(agent.id)
                phase = self.get_phase(task.phase_id)
                
                # Analyze alignment via AOSentry
                coherence = self.analyze_coherence(
                    trajectory=trajectory,
                    phase_instructions=phase.additional_notes,
                    done_definitions=phase.done_definitions
                )
                
                # Intervene if drifting
                if coherence < self.coherence_threshold:
                    self.intervene(agent, phase, coherence)
            
            await asyncio.sleep(self.interval)
    
    def analyze_coherence(
        self,
        trajectory: str,
        phase_instructions: str,
        done_definitions: List[str]
    ) -> float:
        """
        Use AOSentry to score agent alignment with phase goals.
        
        Prompt sent to AOSentry:
        "Agent is working in Phase X with these instructions:
        {phase_instructions}
        ...
        """
        return self.llm_client.chat_completion(...)
```

**Intervention Example**:

```
Agent working in Phase 3 (Validation) starts implementing new features.

Guardian detects:
- Trajectory shows agent writing new code
- Phase 3 is for testing, not implementation
- Coherence score: 0.3 (low)

Guardian sends message:
"⚠️ You're in Phase 3 (Validation). Your job is to TEST existing code,
not implement new features. If you discovered missing functionality,
create a Phase 2 implementation task for another agent."

Agent corrects course:
- Stops coding
- Creates Phase 2 task for missing feature
- Returns to testing
```

### 5. Agent Runtime

**Purpose**: Spawn and manage isolated agent sessions across deployment modes.

**Deployment Modes**:

**A. Local Mode (Development)**
- **Host**: User's local machine (Mac/Linux)
- **Isolation**: tmux sessions + Git worktrees
- **Advantages**: Zero latency, direct access to local tools, free
- **Ideal For**: Single developers, offline work

**B. Hosted Mode (SaaS/Enterprise)**
- **Host**: DevFlow Kubernetes Cluster
- **Isolation**: Ephemeral Docker containers (Firecracker microVMs planned)
- **Advantages**: Scalable, secure, pre-configured environments
- **Ideal For**: Teams, complex workflows, standard environments

**Isolation Strategy (Local Mode)**:
```python
class AgentRuntime:
    """Manages agent lifecycle and isolation."""
    
    def spawn_agent(
        self,
        phase: Phase,
        task: Task
    ) -> Agent:
        """
        Spawn new agent for task.
        
        Isolation mechanisms:
        1. tmux session (separate terminal)
        2. Git worktree (separate code copy)
        3. Virtual environment (separate dependencies)
        """
```

---

## Task Creation Patterns

### 1. Linear Progression

**Scenario**: Simple sequential workflow

```
Phase 1 Agent:
- Analyzes requirements
- Creates single Phase 2 task

Phase 2 Agent:
- Implements feature
- Creates single Phase 3 task

Phase 3 Agent:
- Tests implementation
- Marks workflow complete
```

### 2. Parallel Expansion

**Scenario**: Multiple independent components

```
Phase 1 Agent:
- Identifies 5 components
- Creates 5 Phase 2 tasks (parallel)

5x Phase 2 Agents:
- Each implements one component
- Each creates Phase 3 validation task

5x Phase 3 Agents:
- Each validates one component
```

### 3. Discovery Branching

**Scenario**: Agent discovers optimization opportunity

```
Phase 3 Agent (Testing API):
- Tests pass ✓
- Discovers: "Auth caching pattern could speed up all routes"
- Creates Phase 1 investigation task
- Continues testing

Phase 1 Agent (Investigation):
- Analyzes caching pattern
- Confirms viable
- Creates Phase 2 implementation task

Phase 2 Agent (Implementation):
- Applies caching to all routes
- Creates Phase 3 validation task

Phase 3 Agent (Validation):
- Tests optimization
- Confirms 40% speedup
- Marks done
```

### 4. Bug Fix Loop

**Scenario**: Tests fail, need fixes

```
Phase 3 Agent (Testing):
- Tests fail ❌
- Creates Phase 2 bug fix task
- Marks original test task as blocked

Phase 2 Agent (Fix):
- Fixes bug
- Creates Phase 3 retest task
- Marks fix done (unblocks original test)

Phase 3 Agent (Retest):
- Tests pass ✓
- Marks done
```

---

## API Specification

### REST Endpoints

#### 1. Create Phase
```
POST /api/workflow/phases
Content-Type: application/json

Request:
{
  "name": "analysis",
  "description": "Analyze requirements",
  "done_definitions": [
    "Requirements documented",
    "Components identified",
    "Phase 2 tasks created"
  ],
  "additional_notes": "Break down requirements...",
  "working_directory": "/path/to/project"
}

Response:
{
  "phase_id": 1,
  "status": "created"
}
```

#### 2. Create Task
```
POST /api/workflow/tasks
Content-Type: application/json

Request:
{
  "description": "Implement JWT authentication",
  "phase_id": 2,
  "priority": "high",
  "blocked_by": [],
  "tags": ["authentication", "security"],
  "created_by": "agent-123"
}

Response:
{
  "task_id": "task-456",
  "status": "pending",
  "kanban_column": "backlog"
}
```

#### 3. Claim Task
```
POST /api/workflow/tasks/claim
Content-Type: application/json

Request:
{
  "agent_id": "agent-789",
  "phase_id": 2
}

Response:
{
  "task": {
    "id": "task-456",
    "description": "Implement JWT authentication",
    "phase_id": 2,
    "status": "in_progress",
    "assigned_agent_id": "agent-789"
  }
}
```

#### 4. Update Task Status
```
PUT /api/workflow/tasks/{task_id}/status
Content-Type: application/json

Request:
{
  "status": "done",
  "result": "JWT auth implemented with refresh tokens"
}

Response:
{
  "task_id": "task-456",
  "status": "done",
  "completed_at": "2025-11-18T14:30:00Z",
  "unblocked_tasks": ["task-457", "task-458"]
}
```

#### 5. Get Kanban Board
```
GET /api/workflow/kanban

Response:
{
  "columns": {
    "backlog": [
      {
        "id": "task-001",
        "description": "Analyze authentication requirements",
        "phase_id": 1,
        "priority": "high",
        "blocked_by": []
      }
    ],
    "ready": [...],
    "in_progress": [...],
    "review": [...],
    "done": [...]
  },
  "stats": {
    "total_tasks": 25,
    "done": 10,
    "in_progress": 5,
    "blocked": 3
  }
}
```

#### 6. Get Agent Status
```
GET /api/workflow/agents

Response:
{
  "agents": [
    {
      "id": "agent-123",
      "phase_id": 2,
      "task_id": "task-456",
      "status": "active",
      "coherence_score": 0.89,
      "last_action": "Writing authentication logic",
      "started_at": "2025-11-18T14:00:00Z"
    }
  ]
}
```

### MCP Tools

```python
@mcp_tool
def create_task(
    description: str,
    phase_id: int,
    priority: str = "medium",
    blocked_by: List[str] = [],
    tags: List[str] = []
) -> str:
    """
    Create a new task.
    
    Args:
        description: Detailed task description (what needs to be done)
        phase_id: Which phase this task belongs to (1, 2, 3, etc.)
        priority: "high", "medium", or "low"
        blocked_by: List of task IDs that must complete first
        tags: Tags for organization
    
    Returns:
        Task ID
    """
    pass

@mcp_tool
def update_task_status(
    task_id: str,
    status: str,
    result: Optional[str] = None
) -> Dict:
    """
    Update task status.
    
    Args:
        task_id: Task to update
        status: "in_progress", "done", "failed"
        result: Summary of work completed
    
    Returns:
        Updated task info + unblocked tasks
    """
    pass

@mcp_tool
def get_my_task() -> Optional[Task]:
    """
    Get the task currently assigned to this agent.
    
    Returns:
        Task details or None if no task assigned
    """
    pass

@mcp_tool
def get_phase_info(phase_id: int) -> Phase:
    """
    Get information about a phase.
    
    Args:
        phase_id: Phase to query
    
    Returns:
        Phase details including instructions and done definitions
    """
    pass

@mcp_tool
def get_tasks(
    phase_id: Optional[int] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[Task]:
    """
    Query tasks.
    
    Args:
        phase_id: Filter by phase
        status: Filter by status
        tags: Filter by tags
    
    Returns:
        List of matching tasks
    """
    pass
```

---

## Data Models

### Database Schema (PostgreSQL via Docker)

**Note**: SQLite is not supported. DevFlow requires PostgreSQL with `pgvector` running in Docker for full functionality.

```sql
-- Phases
CREATE TABLE phases (
    id INTEGER PRIMARY KEY,
```

---

## Configuration

```yaml
workflow_engine:
  # Agent spawning
  agent_runtime:
    cli_tool: claude  # claude, opencode, droid
    model: sonnet
    isolation: tmux_worktree  # tmux_worktree, docker, none
    max_concurrent_agents: 10
    agent_timeout_minutes: 60
  
  # Task management
  kanban:
    auto_move_ready: true
    max_ready_tasks: 20
    task_timeout_minutes: 30
    require_review: false
  
  # Guardian monitoring
  guardian:
    enabled: true
    interval_seconds: 60
    coherence_threshold: 0.7
    max_interventions: 3
    escalate_after: 3
  
  # Workflow control
  workflow:
    has_result: true
    result_criteria: "All tests pass and documentation complete"
    on_result_found: stop_all  # stop_all, continue, human_review
    max_iterations: 100
    auto_cleanup_worktrees: true
```

---

## Success Metrics

### Functional
- Task completion rate: > 85%
- Agent alignment (coherence): > 0.8
- Workflow success rate: > 75%

### Performance
- Task spawn latency: < 5 seconds
- Kanban update latency: < 100ms
- Guardian analysis latency: < 2 seconds

### Quality
- Duplicate task rate: < 5%
- Blocked task resolution time: < 10 minutes
- Guardian intervention success rate: > 90%

---

## Integration with External Systems

DevFlow workflows can integrate with external SDLC tools (see **PRD-006: SDLC Tool Integrations**):

**Jira Integration**:
- Tasks in DevFlow sync bidirectionally with Jira issues
- Maintain PRD → Epic → Story → Task → Subtask hierarchy
- Task status updates flow between systems
- Guardian alerts can create Jira comments

**GitHub Integration**:
- Tasks map to GitHub Issues with labels
- Kanban board syncs with GitHub Projects
- Pull requests linked to tasks automatically
- Workflow completion triggers GitHub milestones

**Confluence Integration**:
- Phase documentation stored in Confluence pages
- Workflow results documented automatically
- Guardian intervention logs saved to Confluence

See PRD-006 for complete integration details including OAuth setup, conflict resolution, and hierarchy enforcement.

---

## Future Enhancements

1. **Workflow Templates**: Pre-built phase configurations for common patterns
2. **Learning System**: Improve phase instructions from successful workflows
3. **Conflict Resolution**: Automatic merge conflict handling
4. **Human-in-the-Loop**: Optional approval gates for critical tasks
5. **Resource Optimization**: Intelligent agent spawning based on available resources
6. **Advanced Dependencies**: Support for partial blocking, conditional dependencies
7. **Workflow Visualization**: Real-time graph of task creation and dependencies

---

**End of PRD-003**
