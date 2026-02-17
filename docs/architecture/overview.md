# DevFlow Architecture Overview

This document describes the high-level architecture of DevFlow, a local development environment manager for macOS.

## System Overview

DevFlow consists of three main components:

```
+------------------+     JSON-RPC      +------------------+
|                  |     over stdio    |                  |
|  Native macOS    | <---------------> |  Python Bridge   |
|  SwiftUI App     |                   |  (Handlers)      |
|                  |                   |                  |
+------------------+                   +------------------+
         |                                      |
         v                                      v
+------------------+                   +------------------+
|                  |                   |                  |
|  State Managers  |                   |  DevFlow Core    |
|  (Observable)    |                   |  (Providers)     |
|                  |                   |                  |
+------------------+                   +------------------+
                                               |
                                               v
                                      +------------------+
                                      |                  |
                                      |  Docker / Tools  |
                                      |  (Infrastructure)|
                                      |                  |
                                      +------------------+
```

## Component Descriptions

### 1. Native macOS App (ui-native/)

A SwiftUI application providing the user interface. Built with Swift 6 and the Observation framework.

**Key directories:**
```
ui-native/DevFlow/
├── DevFlowApp.swift          # App entry point
├── ContentView.swift         # Main navigation
├── Models/                   # Data models
├── State/                    # State managers
├── Services/                 # Bridge, RPC client
└── Views/                    # UI components
```

**Technologies:**
- Swift 6 with strict concurrency
- SwiftUI with @Observable macro
- Subprocess package for process management

### 2. Python Bridge (bridge/)

A JSON-RPC 2.0 server that exposes DevFlow functionality to the native app.

**Key directories:**
```
bridge/
├── main.py                   # Entry point
├── server.py                 # RPC server
└── handlers/                 # RPC method handlers
    ├── system.py
    ├── infra.py
    ├── projects.py
    └── ...
```

**Communication:**
- Spawned as subprocess by the native app
- Reads JSON-RPC requests from stdin
- Writes responses to stdout
- Logs to stderr

### 3. DevFlow Core (devflow/)

The Python library implementing core functionality.

**Key directories:**
```
devflow/
├── providers/                # Service providers
│   ├── docker.py
│   ├── traefik.py
│   ├── mkcert.py
│   └── ...
├── tools/                    # Tool management
├── domains/                  # Domain management
├── templates/                # Project templates
└── config/                   # Configuration
```

---

## Data Flow

### Request/Response Cycle

```
1. User clicks "Start Infrastructure" in UI
           |
           v
2. SwiftUI View calls appState.infrastructure.start()
           |
           v
3. InfrastructureState calls bridge.call("infra.start")
           |
           v
4. PythonBridge writes JSON-RPC request to stdin
           |
           v
5. RpcServer reads request, dispatches to InfraHandler.start()
           |
           v
6. InfraHandler uses TraefikProvider to start containers
           |
           v
7. Result returned through JSON-RPC response
           |
           v
8. State updated, UI re-renders automatically
```

### State Management

The app uses a hierarchical state architecture:

```
AppState (Coordinator)
├── NotificationState     # App notifications
├── ConnectionState       # Bridge connection health
├── InfrastructureState   # Traefik, network, domains
├── ProjectsState         # Project management
├── SecretsState          # Secrets management
├── DatabaseState         # Database operations
├── TemplatesState        # Project templates
├── SetupState            # Setup wizard
├── ToolBrowserState      # Tool discovery
├── ConfigState           # Global configuration
└── LogsState             # Container logs
```

Each state manager:
- Is `@Observable` for automatic UI updates
- Is `@MainActor` for thread safety
- Has its own dependencies (bridge, notifications)
- Exposes actions as async methods

---

## IPC Mechanism

### JSON-RPC 2.0 Protocol

The bridge uses JSON-RPC 2.0 over stdio pipes:

```
Native App                              Python Bridge
    |                                        |
    |  {"jsonrpc":"2.0",                     |
    |   "id":1,                              |
    |   "method":"infra.start"}              |
    |  ----------------------------------->  |
    |                                        |
    |           (processing)                 |
    |                                        |
    |  {"jsonrpc":"2.0",                     |
    |   "id":1,                              |
    |   "result":{"success":true}}           |
    |  <-----------------------------------  |
    |                                        |
```

### PythonBridge Actor

```swift
actor PythonBridge {
    private var process: Subprocess?
    private let rpcClient: RpcClient

    func start() async throws {
        // Spawn Python process
        process = try await Subprocess(...)
    }

    func call<T: Decodable>(_ method: String, params: ...) async throws -> T {
        // Send request, await response
        return try await rpcClient.call(method, params: params)
    }
}
```

### RpcClient

```swift
final class RpcClient: @unchecked Sendable {
    private var pendingRequests: [Int: Continuation<Data, Error>]

    func call<T: Decodable>(_ method: String) async throws -> T {
        let request = JsonRpcRequest(id: nextId(), method: method)
        let data = try await sendAndWait(request)
        return try JSONDecoder().decode(T.self, from: data)
    }
}
```

---

## Infrastructure Architecture

### Docker Network

DevFlow creates a Docker network for service communication:

```
devflow-network (bridge)
├── devflow-traefik (reverse proxy)
├── project-a-web
├── project-a-db
├── project-b-web
└── ...
```

### Traefik Integration

Traefik acts as the reverse proxy:

```
Browser                  Traefik                     Services
   |                        |                           |
   | https://app.test       |                           |
   | -------------------->  |                           |
   |                        |  route to app-web:3000    |
   |                        | ------------------------> |
   |                        |                           |
   |    <response>          |       <response>          |
   | <--------------------  | <------------------------ |
```

**Configuration:**
- Dynamic configuration via Docker labels
- TLS termination with mkcert certificates
- Dashboard at port 8080

### Certificate Management

```
mkcert
  |
  v
~/.devflow/certs/
├── cert.pem          # Combined certificate
├── key.pem           # Private key
└── domains.json      # Tracked domains
```

---

## Directory Structure

### Project Root

```
devflow/
├── devflow/              # Python core library
│   ├── providers/        # Service providers
│   ├── tools/            # Tool management
│   ├── domains/          # Domain management
│   ├── templates/        # Project templates
│   └── config/           # Configuration
│
├── bridge/               # JSON-RPC bridge
│   ├── handlers/         # RPC handlers
│   └── server.py         # RPC server
│
├── ui-native/            # macOS app
│   └── DevFlow/
│       ├── Models/
│       ├── State/
│       ├── Services/
│       └── Views/
│
├── tests/                # Python tests
│   └── unit/
│       └── bridge/
│
├── skills/               # Claude Code skills
│
└── docs/                 # Documentation
    ├── api/
    ├── architecture/
    └── wiki/
```

---

## Key Design Decisions

### 1. Separate Native UI and Python Backend

**Rationale:** Leverage native macOS UI capabilities while reusing existing Python DevFlow code.

**Benefits:**
- Native look and feel
- Fast UI rendering
- Reuse of battle-tested Python providers

### 2. JSON-RPC over stdio

**Rationale:** Simple, reliable IPC without network dependencies.

**Benefits:**
- No port conflicts
- Works in sandboxed environments
- Easy debugging (log requests/responses)

### 3. Observable State Pattern

**Rationale:** SwiftUI's preferred way of managing state.

**Benefits:**
- Automatic UI updates
- Clear data flow
- Testable state managers

### 4. Focused State Managers

**Rationale:** Decompose monolithic state into focused units.

**Benefits:**
- Single responsibility
- Easier testing
- Better code organization
- Reduced cognitive load

### 5. Actor-based Bridge

**Rationale:** Ensure thread safety for subprocess communication.

**Benefits:**
- Thread-safe by design
- No data races
- Clear ownership

---

## Error Handling

### Bridge Errors

```swift
enum BridgeError: Error {
    case notConnected
    case invalidResponse
    case timeout(String)
    case rpcError(code: Int, message: String)
}
```

### Reconnection Strategy

```swift
// In ConnectionState
func handleConnectionLost() async {
    // Exponential backoff retry
    var delay: UInt64 = 1_000_000_000 // 1 second
    let maxDelay: UInt64 = 30_000_000_000 // 30 seconds

    for attempt in 1...maxReconnectAttempts {
        try? await Task.sleep(nanoseconds: delay)
        do {
            try await bridge.start()
            return
        } catch {
            delay = min(delay * 2, maxDelay)
        }
    }
}
```

### Health Checks

Periodic pings detect stale connections:

```swift
func startHealthCheck() {
    healthCheckTask = Task {
        while !Task.isCancelled {
            try? await Task.sleep(for: .seconds(30))
            await ping()
        }
    }
}
```

---

## Testing Strategy

### Python Tests

```
tests/unit/bridge/
├── test_logs_handler.py
├── test_domains_handler.py
├── test_tools_handler.py
└── ...
```

Run with: `pytest tests/`

### Swift Tests

```
DevFlowTests/
├── RpcClientTests.swift
└── ModelTests.swift

DevFlowUITests/
└── DevFlowUITests.swift
```

Run with: `xcodebuild test -scheme DevFlow`

---

## Performance Considerations

### 1. Parallel Tool Calls

Independent operations run in parallel:

```swift
async let infra: Void = infrastructureManager.refresh()
async let proj: Void = projectsManager.load()
async let conf: Void = configManager.load()
_ = await (infra, proj, conf)
```

### 2. Polling Optimization

Only poll when infrastructure is running:

```swift
func startPolling() {
    pollingTask = Task {
        while !Task.isCancelled {
            if !isLoadingInfra {
                await refreshSilently()
            }
            try? await Task.sleep(for: .seconds(10))
        }
    }
}
```

### 3. Silent Refreshes

Polling doesn't show loading indicators:

```swift
private func refreshSilently() async {
    do {
        infraStatus = try await bridge.call("infra.status")
    } catch {
        // Silently ignore errors during polling
    }
}
```

---

## Security Considerations

### 1. No Network Exposure

The RPC bridge communicates via stdio, not network sockets.

### 2. Secrets Handling

- Secrets stored via system keychain or password managers
- Never logged or transmitted insecurely
- Masked in UI

### 3. Privileged Operations

Operations requiring sudo (hosts file, ports < 1024) use:

```swift
PrivilegedInstaller.runWithPrivileges(command)
```

This triggers macOS authentication dialog.

---

## Future Considerations

### Potential Improvements

1. **WebSocket Support:** For real-time log streaming
2. **Plugin System:** For custom providers/tools
3. **Multi-machine Support:** Via Docker contexts
4. **Windows/Linux Ports:** Via platform-specific UIs

### Technical Debt

1. Some views still access AppState directly (migration ongoing)
2. Error messages could be more user-friendly
3. Test coverage could be improved for UI components
