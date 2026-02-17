# DevFlow RPC API Reference

This document describes the JSON-RPC 2.0 API exposed by the DevFlow Python bridge. The bridge communicates via stdio pipes, accepting JSON-RPC requests on stdin and returning responses on stdout.

## Protocol

All requests must follow the JSON-RPC 2.0 specification:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "namespace.method",
  "params": {}
}
```

Responses follow the standard format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {}
}
```

Or for errors:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request"
  }
}
```

---

## Namespaces

| Namespace | Description |
|-----------|-------------|
| `system` | Health checks and system information |
| `setup` | Tool installation and setup wizard |
| `config` | Global and project configuration |
| `projects` | Project management |
| `infra` | Infrastructure (Traefik, Docker network) |
| `context` | Docker context management |
| `db` | Database operations |
| `deploy` | Deployment operations |
| `secrets` | Secrets management |
| `dev` | Development server operations |
| `templates` | Project templates |
| `tools` | Tool browser and discovery |
| `domains` | Domain and certificate management |
| `logs` | Container log viewing |

---

## system.*

### system.ping

Health check endpoint.

**Parameters:** None

**Returns:**
```json
{
  "pong": true,
  "timestamp": 1706635200.123
}
```

### system.get_info

Get system information.

**Parameters:** None

**Returns:**
```json
{
  "platform": "darwin",
  "arch": "arm64",
  "python_version": "3.12.0",
  "devflow_version": "0.2.8"
}
```

---

## setup.*

### setup.get_platform_info

Get platform-specific information for setup.

**Parameters:** None

**Returns:**
```json
{
  "platform": "darwin",
  "arch": "arm64",
  "is_wsl": false,
  "has_homebrew": true,
  "has_mise": true
}
```

### setup.get_categories

Get tool categories.

**Parameters:** None

**Returns:**
```json
{
  "categories": [
    {"id": "languages", "name": "Languages", "icon": "code"},
    {"id": "databases", "name": "Databases", "icon": "database"}
  ]
}
```

### setup.get_essential_tools

Get list of essential tools for development.

**Parameters:** None

**Returns:**
```json
[
  {
    "id": "docker",
    "name": "Docker",
    "description": "Container runtime",
    "installed": true,
    "version": "24.0.7"
  }
]
```

### setup.get_tool

Get details for a specific tool.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tool_id` | string | Yes | Tool identifier |

**Returns:**
```json
{
  "id": "node",
  "name": "Node.js",
  "description": "JavaScript runtime",
  "installed": true,
  "version": "20.10.0",
  "install_methods": ["mise", "homebrew"]
}
```

### setup.install

Install a tool.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tool_id` | string | Yes | Tool identifier |
| `method` | string | No | Installation method |

**Returns:**
```json
{
  "success": true,
  "message": "Installed node 20.10.0"
}
```

### setup.install_multiple

Install multiple tools.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tool_ids` | string[] | Yes | List of tool identifiers |

**Returns:**
```json
{
  "success": true,
  "results": [
    {"tool_id": "node", "success": true},
    {"tool_id": "python", "success": true}
  ]
}
```

### setup.get_setup_wizard_status

Get setup wizard completion status.

**Parameters:** None

**Returns:**
```json
{
  "completed": false,
  "steps": [
    {"id": "tools", "completed": true},
    {"id": "infra", "completed": false}
  ],
  "missing_tools": ["mkcert"]
}
```

### setup.get_recommended_tools

Get recommended tools based on detected projects.

**Parameters:** None

**Returns:**
```json
{
  "tools": [
    {"id": "node", "reason": "package.json detected"}
  ]
}
```

---

## config.*

### config.get_global

Get global DevFlow configuration.

**Parameters:** None

**Returns:**
```json
{
  "base_domain": "test",
  "traefik_port": 80,
  "traefik_dashboard_port": 8080,
  "dns_enabled": true,
  "docker_host": null,
  "secrets_provider": "system"
}
```

### config.set_global

Update global configuration.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `base_domain` | string | No | Base domain for projects |
| `traefik_port` | int | No | HTTP port |
| `traefik_dashboard_port` | int | No | Dashboard port |
| `dns_enabled` | bool | No | Enable local DNS |
| `docker_host` | string | No | Docker host URL |
| `secrets_provider` | string | No | Default secrets provider |

**Returns:**
```json
{
  "success": true
}
```

### config.get_project

Get project-specific configuration.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Project path |

**Returns:**
```json
{
  "domain": "myproject.test",
  "port": 3000,
  "commands": {
    "start": "npm run dev",
    "build": "npm run build"
  }
}
```

---

## projects.*

### projects.list

List all registered projects.

**Parameters:** None

**Returns:**
```json
{
  "projects": [
    {
      "id": "abc123",
      "name": "my-project",
      "path": "/Users/user/projects/my-project",
      "domain": "my-project.test",
      "status": "running"
    }
  ]
}
```

### projects.add

Add a project.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Project path |

**Returns:**
```json
{
  "id": "abc123",
  "name": "my-project",
  "path": "/Users/user/projects/my-project"
}
```

### projects.remove

Remove a project from DevFlow.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Project path |

**Returns:**
```json
{
  "success": true
}
```

### projects.get_detail

Get detailed project information including services.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Project path |

**Returns:**
```json
{
  "project": { ... },
  "services": [
    {
      "name": "web",
      "status": "running",
      "image": "node:20",
      "container_id": "abc123",
      "ports": ["3000:3000"]
    }
  ],
  "ports": [
    {"service": "web", "host_port": 3000, "container_port": 3000}
  ],
  "volumes": [
    {"service": "web", "host_path": "./", "container_path": "/app"}
  ],
  "has_compose_file": true,
  "compose_file_path": "/path/to/docker-compose.yml"
}
```

---

## infra.*

### infra.status

Get infrastructure status.

**Parameters:** None

**Returns:**
```json
{
  "traefik_running": true,
  "traefik_healthy": true,
  "network_exists": true,
  "mkcert_installed": true,
  "certs_valid": true
}
```

### infra.start

Start development infrastructure.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `force_recreate` | bool | No | Force recreate containers |

**Returns:**
```json
{
  "success": true,
  "message": "Infrastructure started"
}
```

### infra.stop

Stop development infrastructure.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `remove_volumes` | bool | No | Remove volumes |
| `remove_network` | bool | No | Remove network |

**Returns:**
```json
{
  "success": true,
  "message": "Infrastructure stopped"
}
```

---

## domains.*

### domains.list

List all configured domains.

**Parameters:** None

**Returns:**
```json
{
  "domains": [
    {
      "domain": "*.test",
      "is_wildcard": true,
      "source": "default",
      "in_hosts_file": true,
      "has_cert": true
    }
  ],
  "cert_info": {
    "exists": true,
    "valid": true,
    "expires_at": "2025-01-01T00:00:00Z",
    "domains_count": 5
  },
  "hosts_entries": ["127.0.0.1 myapp.test"]
}
```

### domains.add

Add a domain.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `domain` | string | Yes | Domain to add |
| `source` | string | No | Source (user, project) |

**Returns:**
```json
{
  "success": true,
  "message": "Domain added",
  "needs_cert_regen": true
}
```

### domains.remove

Remove a domain.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `domain` | string | Yes | Domain to remove |

**Returns:**
```json
{
  "success": true,
  "message": "Domain removed",
  "needs_cert_regen": true
}
```

### domains.regenerate_certs

Regenerate SSL certificates for all domains.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "message": "Certificates regenerated",
  "domains_count": 5
}
```

### domains.update_hosts

Update /etc/hosts file with domain entries.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "message": "Hosts file updated",
  "entries_added": 3
}
```

---

## tools.*

### tools.search

Search for tools in the tool browser.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | No | Search query |
| `categories` | string[] | No | Filter by categories |
| `sources` | string[] | No | Filter by sources |
| `installed_only` | bool | No | Show installed only |
| `limit` | int | No | Results limit (default 20) |
| `offset` | int | No | Results offset |

**Returns:**
```json
{
  "tools": [...],
  "total": 150,
  "has_more": true
}
```

### tools.get_categories

Get available tool categories.

**Parameters:** None

**Returns:**
```json
{
  "categories": [
    {"id": "languages", "name": "Languages", "count": 25}
  ]
}
```

### tools.get_sources

Get available tool sources.

**Parameters:** None

**Returns:**
```json
{
  "sources": [
    {"id": "mise", "name": "mise", "count": 100},
    {"id": "homebrew", "name": "Homebrew", "count": 50}
  ]
}
```

### tools.install

Install a tool from the browser.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tool_id` | string | Yes | Tool identifier |

**Returns:**
```json
{
  "success": true,
  "message": "Tool installed"
}
```

### tools.detect_installed

Detect which tools from a list are installed.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tool_ids` | string[] | Yes | Tool identifiers |

**Returns:**
```json
{
  "installed": {
    "node": true,
    "python": true,
    "go": false
  }
}
```

### tools.refresh_cache

Refresh the tool cache.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `force` | bool | No | Force refresh |

**Returns:**
```json
{
  "success": true,
  "tools_count": 150
}
```

---

## templates.*

### templates.list_templates

List available project templates.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `category` | string | No | Filter by category |
| `search` | string | No | Search query |

**Returns:**
```json
{
  "templates": [
    {
      "id": "nextjs-starter",
      "name": "Next.js Starter",
      "description": "Modern React framework",
      "category": "frontend",
      "source": "builtin"
    }
  ]
}
```

### templates.get_template

Get template details.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `template_id` | string | Yes | Template identifier |

**Returns:**
```json
{
  "id": "nextjs-starter",
  "name": "Next.js Starter",
  "description": "Modern React framework",
  "steps": [...],
  "required_tools": ["node", "npm"]
}
```

### templates.check_required_tools

Check if required tools are installed.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `template_id` | string | Yes | Template identifier |

**Returns:**
```json
{
  "all_installed": false,
  "tools": [
    {"id": "node", "installed": true},
    {"id": "pnpm", "installed": false}
  ]
}
```

### templates.create_project

Create a new project from a template.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `template_id` | string | Yes | Template identifier |
| `values` | object | Yes | Wizard step values |

**Returns:**
```json
{
  "success": true,
  "project_path": "/Users/user/projects/my-app",
  "message": "Project created successfully"
}
```

### templates.import_template

Import a template from a Git repository.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `git_url` | string | Yes | Git repository URL |
| `branch` | string | No | Branch name |
| `subdirectory` | string | No | Subdirectory path |

**Returns:**
```json
{
  "success": true,
  "template_id": "imported-template"
}
```

---

## logs.*

### logs.list_containers

List containers available for log viewing.

**Parameters:** None

**Returns:**
```json
{
  "containers": [
    {
      "id": "abc123",
      "name": "devflow-traefik",
      "status": "running",
      "created": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### logs.get_logs

Get logs from a container.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `container` | string | Yes | Container name or ID |
| `lines` | int | No | Number of lines (default 100) |
| `since` | string | No | Since timestamp |

**Returns:**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "level": "info",
      "message": "Server started"
    }
  ],
  "container": "devflow-traefik"
}
```

### logs.get_traefik_logs

Get Traefik access logs.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `lines` | int | No | Number of lines (default 100) |
| `since` | string | No | Since timestamp |

**Returns:**
```json
{
  "logs": [...],
  "container": "devflow-traefik"
}
```

---

## secrets.*

### secrets.list

List secrets for a project.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Project path |
| `environment` | string | No | Environment filter |
| `source` | string | No | Source filter |

**Returns:**
```json
{
  "secrets": [
    {
      "key": "DATABASE_URL",
      "value": "***",
      "provider": "system",
      "project_id": "abc123"
    }
  ]
}
```

### secrets.set

Set a secret.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Project path |
| `key` | string | Yes | Secret key |
| `value` | string | Yes | Secret value |
| `provider` | string | No | Secrets provider |

**Returns:**
```json
{
  "success": true
}
```

### secrets.delete

Delete a secret.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Project path |
| `key` | string | Yes | Secret key |

**Returns:**
```json
{
  "success": true
}
```

---

## dev.*

### dev.start

Start development server for a project.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Project path |
| `service` | string | No | Specific service |
| `detach` | bool | No | Run detached |

**Returns:**
```json
{
  "success": true,
  "message": "Development server started",
  "url": "https://myapp.test"
}
```

### dev.stop

Stop development server for a project.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Project path |
| `service` | string | No | Specific service |

**Returns:**
```json
{
  "success": true,
  "message": "Development server stopped"
}
```

---

## db.*

### db.create

Create a new database.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Project path |
| `name` | string | Yes | Database name |

**Returns:**
```json
{
  "success": true,
  "connection_string": "postgresql://..."
}
```

---

## context.*

### context.list_contexts

List Docker contexts.

**Parameters:** None

**Returns:**
```json
{
  "contexts": [
    {
      "name": "default",
      "is_current": true,
      "endpoint": "unix:///var/run/docker.sock"
    }
  ]
}
```

### context.create_context

Create a new Docker context.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Context name |
| `host` | string | Yes | Docker host |
| `ssh_user` | string | No | SSH username |

**Returns:**
```json
{
  "success": true,
  "message": "Context created"
}
```

### context.delete_context

Delete a Docker context.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Context name |

**Returns:**
```json
{
  "success": true
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `-32700` | Parse error - Invalid JSON |
| `-32600` | Invalid Request |
| `-32601` | Method not found |
| `-32602` | Invalid params |
| `-32603` | Internal error |
| `-32000` | Application error (custom) |

---

## Usage Example

```bash
# Send a ping request
echo '{"jsonrpc":"2.0","id":1,"method":"system.ping"}' | python -m bridge.main

# Response:
# {"jsonrpc":"2.0","id":1,"result":{"pong":true,"timestamp":1706635200.123}}
```

```swift
// Swift usage via PythonBridge
let response: PingResponse = try await bridge.call("system.ping")
print(response.pong) // true
```
