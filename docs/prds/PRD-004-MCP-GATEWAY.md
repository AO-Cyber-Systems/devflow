# PRD-004: MCP Gateway Service

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)

---

## Overview

The MCP Gateway Service provides a unified Model Context Protocol (MCP) interface that allows AI agents to access both the Knowledge Hub and Workflow Engine through standardized tools. This service acts as the integration layer, exposing DevFlow's capabilities to Claude Code, OpenCode, Cursor, Windsurf, and other MCP-compatible AI assistants.

---

## Goals

### Primary Goals
1. Provide standardized MCP tools for knowledge access and workflow management
2. Enable seamless integration with multiple AI coding assistants
3. Ensure consistent tool behavior across different client implementations
4. Support both SSE (Server-Sent Events) and stdio transport modes

### Secondary Goals
1. Enable tool discovery and schema validation
2. Provide usage analytics and rate limiting
3. Support authentication and authorization
4. Enable graceful degradation when backend services are unavailable

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  MCP Gateway Service                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │            MCP Protocol Handler                      │  │
│  │                                                       │  │
│  │  - Tool Registry                                     │  │
│  │  - Schema Validation                                 │  │
│  │  - Request Routing                                   │  │
│  │  - Response Formatting                               │  │
│  └─────────────────────────────────────────────────────┘  │
│                          │                                  │
│         ┌────────────────┼────────────────┐               │
│         │                │                │               │
│    ┌────▼────┐     ┌────▼────┐     ┌────▼────┐          │
│    │ Knowledge│     │Workflow │     │  Memory │          │
│    │  Tools   │     │ Tools   │     │  Tools  │          │
│    │          │     │         │     │         │          │
│    │ -search  │     │ -create │     │ -save   │          │
│    │ -get_src │     │ -update │     │ -query  │          │
│    │ -list    │     │ -claim  │     │ -delete │          │
│    └────┬────┘     └────┬────┘     └────┬────┘          │
│         │                │                │               │
│         └────────────────┼────────────────┘               │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Backend Service Clients                 │  │
│  │                                                       │  │
│  │  - Knowledge Hub Client (HTTP)                       │  │
│  │  - Workflow Engine Client (HTTP)                     │  │
│  │  - Qdrant Client (gRPC)                              │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │ Claude  │      │OpenCode │      │ Cursor  │
   │  Code   │      │         │      │         │
   └─────────┘      └─────────┘      └─────────┘
```

---

## MCP Tool Categories

### 1. Knowledge Tools

Tools for accessing the knowledge base.

#### `search_knowledge`
Search for relevant information in the knowledge base.

```python
@mcp_tool
async def search_knowledge(
    query: str,
    mode: Literal["semantic", "hybrid", "reranked"] = "hybrid",
    top_k: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    include_code_examples: bool = False
) -> SearchResult:
    """
    Search the project knowledge base.
    
    Args:
        query: What to search for
        mode: Search strategy
            - semantic: Vector similarity only
            - hybrid: Vector + keyword search
            - reranked: Hybrid + LLM reranking (slower, more accurate)
        top_k: Number of results to return
        filters: Optional filters
            - tags: List[str] - Filter by tags
            - sources: List[str] - Filter by source IDs
            - has_code: bool - Only results with code examples
        include_code_examples: Extract and include code blocks
    
    Returns:
        {
            "results": [
                {
                    "content": str,
                    "source": str,
                    "url": str,
                    "score": float,
                    "metadata": {...},
                    "code_examples": [...] if requested
                }
            ],
            "total_results": int,
            "search_time_ms": int
        }
    
    Example:
        results = search_knowledge(
            query="How to implement JWT authentication?",
            mode="reranked",
            filters={"tags": ["authentication", "security"]},
            include_code_examples=True
        )
    """
    pass
```

#### `get_code_examples`
Get code examples for a specific topic.

```python
@mcp_tool
async def get_code_examples(
    topic: str,
    language: Optional[str] = None,
    top_k: int = 5
) -> CodeExampleResult:
    """
    Get code examples from the knowledge base.
    
    Args:
        topic: What the code should demonstrate
        language: Programming language filter
        top_k: Number of examples
    
    Returns:
        {
            "examples": [
                {
                    "code": str,
                    "language": str,
                    "context": str,
                    "source": str,
                    "url": str
                }
            ]
        }
    
    Example:
        examples = get_code_examples(
            topic="JWT token validation",
            language="python"
        )
    """
    pass
```

#### `list_knowledge_sources`
List available knowledge sources.

```python
@mcp_tool
async def list_knowledge_sources(
    tags: Optional[List[str]] = None,
    status: Optional[str] = None
) -> SourceList:
    """
    List knowledge sources in the system.
    
    Args:
        tags: Filter by tags
        status: Filter by status (active, indexing, error)
    
    Returns:
        {
            "sources": [
                {
                    "id": str,
                    "title": str,
                    "type": str,
                    "url": str,
                    "tags": List[str],
                    "chunk_count": int,
                    "last_updated": str
                }
            ]
        }
    """
    pass
```

#### `get_source_info`
Get detailed information about a knowledge source.

```python
@mcp_tool
async def get_source_info(source_id: str) -> SourceInfo:
    """
    Get detailed information about a knowledge source.
    
    Args:
        source_id: Source ID to query
    
    Returns:
        {
            "id": str,
            "title": str,
            "description": str,
            "type": str,
            "url": str,
            "tags": List[str],
            "priority": int,
            "chunk_count": int,
            "created_at": str,
            "updated_at": str,
            "metadata": {...}
        }
    """
    pass
```

### 2. Workflow Tools

Tools for task and workflow management.

#### `create_task`
Create a new task in any phase.

```python
@mcp_tool
async def create_task(
    description: str,
    phase_id: int,
    priority: Literal["high", "medium", "low"] = "medium",
    blocked_by: List[str] = [],
    tags: List[str] = [],
    metadata: Optional[Dict[str, Any]] = None
) -> TaskCreated:
    """
    Create a new task for the workflow.
    
    Use this when you discover work that needs to be done:
    - Phase 1: Investigation, analysis, planning
    - Phase 2: Implementation, building, fixing
    - Phase 3: Testing, validation, verification
    
    Args:
        description: Detailed description of what needs to be done
        phase_id: Which phase this task belongs to
        priority: Task priority
        blocked_by: List of task IDs that must complete first
        tags: Tags for organization
        metadata: Additional context
    
    Returns:
        {
            "task_id": str,
            "status": str,
            "kanban_column": str
        }
    
    Example:
        task = create_task(
            description=\"\"\"
            Phase 2: Implement JWT Authentication
            
            Requirements:
            - /auth/login endpoint returns JWT
            - /auth/refresh endpoint for token renewal
            - All API endpoints validate JWT
            - Store tokens in Redis
            
            Acceptance criteria:
            - Tests cover happy path and errors
            - Documentation updated
            \"\"\",
            phase_id=2,
            priority="high",
            tags=["authentication", "security"]
        )
    """
    pass
```

#### `update_task_status`
Update your task status.

```python
@mcp_tool
async def update_task_status(
    task_id: str,
    status: Literal["in_progress", "done", "failed"],
    result: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> TaskUpdated:
    """
    Update task status.
    
    IMPORTANT: Mark your task as 'done' when you complete all requirements!
    
    Args:
        task_id: Task to update
        status: New status
        result: Summary of what was accomplished
        metadata: Additional information
    
    Returns:
        {
            "task_id": str,
            "status": str,
            "completed_at": str (if done),
            "unblocked_tasks": List[str]
        }
    
    Example:
        update_task_status(
            task_id="task-123",
            status="done",
            result="JWT auth implemented with refresh tokens. All tests pass."
        )
    """
    pass
```

#### `claim_task`
Claim the next available task for your phase.

```python
@mcp_tool
async def claim_task(phase_id: int) -> Optional[Task]:
    """
    Claim next available task for your phase.
    
    Args:
        phase_id: Your phase ID
    
    Returns:
        Task details or None if no tasks available
        {
            "id": str,
            "description": str,
            "phase_id": int,
            "priority": str,
            "created_by": str,
            "created_at": str
        }
    """
    pass
```

#### `get_my_task`
Get information about your current task.

```python
@mcp_tool
async def get_my_task() -> Optional[Task]:
    """
    Get your currently assigned task.
    
    Returns:
        Current task details or None
    """
    pass
```

#### `get_tasks`
Query tasks with filters.

```python
@mcp_tool
async def get_tasks(
    phase_id: Optional[int] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> TaskList:
    """
    Query tasks.
    
    Args:
        phase_id: Filter by phase
        status: Filter by status
        tags: Filter by tags
    
    Returns:
        {
            "tasks": [
                {
                    "id": str,
                    "description": str,
                    "phase_id": int,
                    "status": str,
                    "priority": str,
                    "assigned_agent_id": str,
                    "created_at": str
                }
            ]
        }
    """
    pass
```

#### `get_phase_info`
Get information about a phase.

```python
@mcp_tool
async def get_phase_info(phase_id: int) -> Phase:
    """
    Get phase details including instructions and requirements.
    
    Args:
        phase_id: Phase to query
    
    Returns:
        {
            "id": int,
            "name": str,
            "description": str,
            "done_definitions": List[str],
            "additional_notes": str,
            "working_directory": str
        }
    """
    pass
```

#### `get_kanban_board`
Get current Kanban board state.

```python
@mcp_tool
async def get_kanban_board() -> KanbanBoard:
    """
    Get current Kanban board with all tasks.
    
    Returns:
        {
            "columns": {
                "backlog": [...],
                "ready": [...],
                "in_progress": [...],
                "review": [...],
                "done": [...]
            },
            "stats": {
                "total_tasks": int,
                "done": int,
                "in_progress": int,
                "blocked": int
            }
        }
    """
    pass
```

### 3. Memory Tools

Tools for storing and retrieving agent memories.

#### `save_memory`
Save a memory to the vector store.

```python
@mcp_tool
async def save_memory(
    content: str,
    category: str,
    tags: List[str] = [],
    metadata: Optional[Dict[str, Any]] = None
) -> MemorySaved:
    """
    Save important information for future reference.
    
    Use this to remember:
    - Important decisions made
    - Patterns discovered
    - Problems encountered and solutions
    - Project-specific conventions
    
    Args:
        content: What to remember
        category: Category (decision, pattern, problem, convention)
        tags: Tags for organization
        metadata: Additional context
    
    Returns:
        {
            "memory_id": str,
            "status": str
        }
    
    Example:
        save_memory(
            content=\"\"\"
            Found that authentication caching pattern reduces
            database queries by 60%. Applied to all API routes
            with significant performance improvement.
            \"\"\",
            category="pattern",
            tags=["performance", "caching", "authentication"]
        )
    """
    pass
```

#### `query_memories`
Search saved memories.

```python
@mcp_tool
async def query_memories(
    query: str,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    top_k: int = 10
) -> MemoryList:
    """
    Search saved memories.
    
    Args:
        query: What to search for
        category: Filter by category
        tags: Filter by tags
        top_k: Number of results
    
    Returns:
        {
            "memories": [
                {
                    "content": str,
                    "category": str,
                    "tags": List[str],
                    "created_at": str,
                    "score": float
                }
            ]
        }
    """
    pass
```

#### `delete_memory`
Delete a memory.

```python
@mcp_tool
async def delete_memory(memory_id: str) -> MemoryDeleted:
    """
    Delete a saved memory.
    
    Args:
        memory_id: Memory to delete
    
    Returns:
        {
            "memory_id": str,
            "status": str
        }
    """
    pass
```

### 4. Agent Coordination Tools

Tools for agent awareness and coordination.

#### `get_agent_status`
Get status of all active agents.

```python
@mcp_tool
async def get_agent_status() -> AgentStatusList:
    """
    Get status of all active agents.
    
    Returns:
        {
            "agents": [
                {
                    "id": str,
                    "phase_id": int,
                    "task_id": str,
                    "status": str,
                    "coherence_score": float,
                    "last_action": str,
                    "started_at": str
                }
            ]
        }
    """
    pass
```

#### `send_message_to_agent`
Send a message to another agent.

```python
@mcp_tool
async def send_message_to_agent(
    agent_id: str,
    message: str
) -> MessageSent:
    """
    Send a message to another agent.
    
    Args:
        agent_id: Target agent
        message: Message content
    
    Returns:
        {
            "status": str,
            "delivered_at": str
        }
    """
    pass
```

---

## Protocol Implementation

### Transport Modes

#### 1. SSE (Server-Sent Events)
For web-based clients and remote connections.

```python
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

app = FastAPI()

@app.get("/mcp/sse")
async def mcp_sse_endpoint():
    """SSE endpoint for MCP protocol."""
    
    async def event_generator():
        while True:
            # Receive tool call request
            request = await receive_mcp_request()
            
            # Execute tool
            result = await execute_tool(
                tool_name=request.tool,
                args=request.args
            )
            
            # Send response
            yield {
                "event": "tool_response",
                "data": json.dumps(result)
            }
    
    return EventSourceResponse(event_generator())
```

#### 2. stdio (Standard Input/Output)
For local CLI tools like Claude Code.

```python
#!/usr/bin/env python3
import sys
import json
import asyncio

async def stdio_mcp_server():
    """stdio MCP server for Claude Code."""
    
    while True:
        # Read request from stdin
        line = sys.stdin.readline()
        if not line:
            break
        
        request = json.loads(line)
        
        # Execute tool
        result = await execute_tool(
            tool_name=request["tool"],
            args=request["args"]
        )
        
        # Write response to stdout
        sys.stdout.write(json.dumps(result) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(stdio_mcp_server())
```

### Tool Registry

```python
from typing import Callable, Dict, Any
from pydantic import BaseModel

class ToolDefinition(BaseModel):
    """MCP tool definition."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: Callable

class MCPToolRegistry:
    """Registry of available MCP tools."""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
    
    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any]
    ):
        """Decorator to register a tool."""
        def decorator(handler: Callable):
            self.tools[name] = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                handler=handler
            )
            return handler
        return decorator
    
    def get_tool_schema(self, name: str) -> Dict[str, Any]:
        """Get JSON schema for a tool."""
        tool = self.tools[name]
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }
    
    async def execute_tool(
        self,
        name: str,
        args: Dict[str, Any]
    ) -> Any:
        """Execute a tool with validation."""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        
        tool = self.tools[name]
        
        # Validate args against schema
        # (use jsonschema library)
        
        # Execute handler
        return await tool.handler(**args)

# Global registry
registry = MCPToolRegistry()

# Register tools
@registry.register(
    name="search_knowledge",
    description="Search the knowledge base",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "mode": {"type": "string", "enum": ["semantic", "hybrid", "reranked"]},
            "top_k": {"type": "integer", "default": 10}
        },
        "required": ["query"]
    }
)
async def search_knowledge_handler(
    query: str,
    mode: str = "hybrid",
    top_k: int = 10
):
    # Implementation
    pass
```

### Request Handling

```python
from pydantic import BaseModel

class MCPRequest(BaseModel):
    """MCP tool call request."""
    tool: str
    args: Dict[str, Any]
    request_id: str

class MCPResponse(BaseModel):
    """MCP tool call response."""
    request_id: str
    result: Any
    error: Optional[str] = None

async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
    """Handle MCP tool call."""
    try:
        # Execute tool
        result = await registry.execute_tool(
            name=request.tool,
            args=request.args
        )
        
        return MCPResponse(
            request_id=request.request_id,
            result=result
        )
    
    except Exception as e:
        return MCPResponse(
            request_id=request.request_id,
            result=None,
            error=str(e)
        )
```

---

## Configuration

### Server Configuration

```yaml
mcp_gateway:
  # Server
  host: 0.0.0.0
  port: 8051
  
  # Transport
  sse_enabled: true
  stdio_enabled: true
  
  # Backend clients
  knowledge_hub_url: http://localhost:8181
  workflow_engine_url: http://localhost:8182
  qdrant_url: http://localhost:6333
  
  # Rate limiting
  rate_limit:
    enabled: true
    requests_per_minute: 100
    burst: 20
  
  # Caching
  cache:
    enabled: true
    ttl_seconds: 300
    max_size_mb: 100
  
  # Monitoring
  telemetry:
    enabled: true
    export_endpoint: http://localhost:9090
```

### Client Configuration

```json
{
  "mcpServers": {
    "devflow": {
      "command": "python",
      "args": ["/path/to/mcp_gateway_client.py"],
      "env": {
        "DEVFLOW_API_URL": "http://localhost:8051"
      }
    }
  }
}
```

---

## API Endpoints

### Tool Discovery

```
GET /mcp/tools

Response:
{
  "tools": [
    {
      "name": "search_knowledge",
      "description": "Search the knowledge base",
      "parameters": {...}
    },
    ...
  ]
}
```

### Health Check

```
GET /mcp/health

Response:
{
  "status": "healthy",
  "backend_services": {
    "knowledge_hub": "up",
    "workflow_engine": "up",
    "qdrant": "up"
  }
}
```

### Metrics

```
GET /mcp/metrics

Response:
{
  "requests_total": 12345,
  "requests_per_minute": 45,
  "errors_total": 23,
  "error_rate": 0.002,
  "avg_response_time_ms": 123,
  "tools": {
    "search_knowledge": {
      "calls": 5432,
      "avg_time_ms": 156
    },
    ...
  }
}
```

---

## Security

### Authentication

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key for MCP access."""
    if not is_valid_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/mcp/tools")
async def get_tools(api_key: str = Depends(verify_api_key)):
    """Get available tools (requires auth)."""
    return {"tools": registry.get_all_schemas()}
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/mcp/execute")
@limiter.limit("100/minute")
async def execute_tool(request: MCPRequest):
    """Execute MCP tool (rate limited)."""
    return await handle_mcp_request(request)
```

---

## Testing

### Unit Tests

```python
import pytest
from mcp_gateway import MCPToolRegistry, handle_mcp_request

@pytest.mark.asyncio
async def test_search_knowledge_tool():
    """Test search_knowledge tool."""
    request = MCPRequest(
        tool="search_knowledge",
        args={"query": "authentication", "top_k": 5},
        request_id="test-123"
    )
    
    response = await handle_mcp_request(request)
    
    assert response.error is None
    assert len(response.result["results"]) <= 5

@pytest.mark.asyncio
async def test_create_task_tool():
    """Test create_task tool."""
    request = MCPRequest(
        tool="create_task",
        args={
            "description": "Test task",
            "phase_id": 2,
            "priority": "high"
        },
        request_id="test-456"
    )
    
    response = await handle_mcp_request(request)
    
    assert response.error is None
    assert "task_id" in response.result
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete workflow via MCP tools."""
    
    # 1. Search knowledge
    search_response = await execute_mcp_tool(
        "search_knowledge",
        {"query": "authentication patterns"}
    )
    assert len(search_response["results"]) > 0
    
    # 2. Create task
    task_response = await execute_mcp_tool(
        "create_task",
        {
            "description": "Implement auth",
            "phase_id": 2
        }
    )
    task_id = task_response["task_id"]
    
    # 3. Update task
    update_response = await execute_mcp_tool(
        "update_task_status",
        {
            "task_id": task_id,
            "status": "done"
        }
    )
    assert update_response["status"] == "done"
```

---

## Success Metrics

### Performance
- Tool execution latency (p95): < 200ms
- SSE connection stability: > 99.9%
- Rate limit bypass rate: < 0.1%

### Reliability
- Tool success rate: > 99%
- Backend service failover time: < 5 seconds
- Error recovery rate: > 95%

### Usage
- Daily tool calls: > 1000
- Most used tools: search_knowledge, create_task, update_task_status
- Client diversity: Claude Code, OpenCode, Cursor, Windsurf

---

## Future Enhancements

1. **Tool Batching**: Execute multiple tools in one request
2. **Streaming Responses**: Stream large results progressively
3. **Tool Composition**: Chain tools together
4. **Custom Tools**: Allow users to register custom MCP tools
5. **GraphQL Support**: Alternative to REST for tool execution
6. **WebSocket Transport**: Bidirectional communication
7. **Tool Versioning**: Support multiple versions of tools

---

**End of PRD-004**
