# Contributing to DevFlow

Thank you for your interest in contributing to DevFlow! This guide will help you get started with development.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Architecture Guidelines](#architecture-guidelines)

---

## Development Setup

### Prerequisites

- **macOS 14.0+** (Sonoma or later)
- **Xcode 16.0+**
- **Python 3.12+**
- **Docker Desktop**
- **mise** (recommended for tool management)

### Clone the Repository

```bash
git clone https://github.com/your/devflow.git
cd devflow
```

### Install Python Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"
```

### Build the Native App

```bash
cd ui-native

# Build for development
xcodebuild -scheme DevFlow -configuration Debug build

# Or open in Xcode
open DevFlow.xcodeproj
```

### Run Tests

```bash
# Python tests
pytest

# Swift tests
cd ui-native
xcodebuild test -scheme DevFlow -destination 'platform=macOS'
```

---

## Project Structure

```
devflow/
├── devflow/              # Python core library
│   ├── providers/        # Docker, Traefik, mkcert providers
│   ├── tools/            # Tool browser and detection
│   ├── domains/          # Domain and certificate management
│   ├── templates/        # Project template system
│   └── config/           # Configuration management
│
├── bridge/               # JSON-RPC bridge for native app
│   ├── handlers/         # RPC method implementations
│   ├── server.py         # RPC server
│   └── main.py           # Entry point
│
├── ui-native/            # macOS SwiftUI application
│   └── DevFlow/
│       ├── Models/       # Data models
│       ├── State/        # Observable state managers
│       ├── Services/     # Bridge, RPC client
│       └── Views/        # UI components
│
├── tests/                # Python test suite
│   └── unit/
│       └── bridge/       # Bridge handler tests
│
├── skills/               # Claude Code skill definitions
│
└── docs/                 # Documentation
    ├── api/              # RPC API reference
    ├── architecture/     # Architecture docs
    └── wiki/             # User documentation
```

---

## Development Workflow

### Running the App

1. **Start the Python bridge manually (for debugging):**
   ```bash
   python -m bridge.main
   ```

2. **Run the native app from Xcode:**
   - Open `ui-native/DevFlow.xcodeproj`
   - Select the DevFlow scheme
   - Press Cmd+R to run

3. **Or run from command line:**
   ```bash
   open ~/Library/Developer/Xcode/DerivedData/DevFlow-*/Build/Products/Debug/DevFlow.app
   ```

### Making Changes

#### Python Changes

1. Make changes to `devflow/` or `bridge/`
2. Run tests: `pytest tests/unit/`
3. The native app will use the updated code on next launch

#### Swift Changes

1. Make changes in Xcode
2. Press Cmd+B to build
3. Press Cmd+R to run

### Adding New RPC Methods

1. **Create or update a handler in `bridge/handlers/`:**
   ```python
   # bridge/handlers/example.py
   class ExampleHandler:
       def my_method(self, param: str) -> dict[str, Any]:
           """Do something."""
           return {"result": param}
   ```

2. **Register the handler in `bridge/main.py`:**
   ```python
   server.register_handler(ExampleHandler(), "example")
   ```

3. **Call from Swift:**
   ```swift
   let result: MyResponse = try await bridge.call("example.my_method", params: ["param": "value"])
   ```

### Adding New Views

1. **Create the view in `ui-native/DevFlow/Views/`:**
   ```swift
   struct MyView: View {
       @Environment(AppState.self) private var appState

       var body: some View {
           Text("Hello")
       }
   }
   ```

2. **Add to Xcode project:**
   - Right-click the appropriate group in Xcode
   - Select "Add Files to DevFlow"
   - Select your new Swift file

3. **Add navigation if needed in `ContentView.swift`**

---

## Code Style

### Python

We use **black** for formatting and **ruff** for linting.

```bash
# Format code
black devflow/ bridge/ tests/

# Lint code
ruff check devflow/ bridge/ tests/
```

**Guidelines:**
- Type hints for all function signatures
- Docstrings for public methods
- Maximum line length: 100 characters

### Swift

We follow Apple's Swift API Design Guidelines.

**Guidelines:**
- Use `@Observable` for state classes
- Use `@MainActor` for UI-related code
- Prefer `async/await` over callbacks
- Use structured concurrency with `Task` and `TaskGroup`

**Naming:**
- Types and protocols: `UpperCamelCase`
- Functions, properties, variables: `lowerCamelCase`
- Constants: `lowerCamelCase`

---

## Testing

### Python Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=devflow --cov=bridge

# Run specific test file
pytest tests/unit/bridge/test_domains_handler.py

# Run specific test
pytest tests/unit/bridge/test_domains_handler.py::TestDomainsHandler::test_add_domain
```

**Writing tests:**
```python
import pytest
from unittest.mock import MagicMock

class TestMyHandler:
    @pytest.fixture
    def handler(self):
        handler = MyHandler()
        handler.provider = MagicMock()
        return handler

    def test_my_method(self, handler):
        result = handler.my_method("test")
        assert result["success"] is True
```

### Swift Tests

```bash
# Run all tests
cd ui-native
xcodebuild test -scheme DevFlow -destination 'platform=macOS'

# Run in Xcode
# Press Cmd+U
```

**Writing tests:**
```swift
import XCTest
@testable import DevFlow

class ModelTests: XCTestCase {
    func testProjectDecoding() throws {
        let json = """
        {"id": "123", "name": "test", "path": "/tmp"}
        """
        let data = json.data(using: .utf8)!
        let project = try JSONDecoder().decode(Project.self, from: data)
        XCTAssertEqual(project.name, "test")
    }
}
```

---

## Pull Request Process

### Before Submitting

1. **Run all tests:**
   ```bash
   pytest
   cd ui-native && xcodebuild test -scheme DevFlow -destination 'platform=macOS'
   ```

2. **Format code:**
   ```bash
   black devflow/ bridge/ tests/
   ruff check --fix devflow/ bridge/ tests/
   ```

3. **Update documentation** if you changed APIs

### PR Guidelines

1. **Keep PRs focused:** One feature or fix per PR
2. **Write descriptive titles:** `feat: Add log viewer` or `fix: Handle connection timeout`
3. **Include context:** Explain why the change is needed
4. **Add tests:** For new functionality or bug fixes
5. **Update docs:** If you changed user-facing behavior

### PR Template

```markdown
## Summary
Brief description of the changes.

## Changes
- Added X
- Updated Y
- Fixed Z

## Test Plan
- [ ] Added unit tests
- [ ] Tested manually
- [ ] Updated documentation

## Screenshots (if UI changes)
[Attach screenshots]
```

### Review Process

1. At least one approval required
2. All tests must pass
3. No unresolved comments
4. Squash and merge preferred

---

## Architecture Guidelines

### State Management

- Use focused state managers (not monolithic AppState)
- State managers should be `@Observable` and `@MainActor`
- Keep state managers single-responsibility

```swift
@Observable
@MainActor
class FeatureState {
    // State
    var items: [Item] = []
    var isLoading = false

    // Dependencies
    @ObservationIgnored private let bridge: PythonBridge
    @ObservationIgnored private let notifications: NotificationState

    // Actions
    func load() async { ... }
}
```

### Bridge Communication

- All bridge calls should be `async throws`
- Use strongly-typed response models
- Handle errors gracefully

```swift
func loadItems() async {
    isLoading = true
    defer { isLoading = false }

    do {
        let response: ItemsResponse = try await bridge.call("items.list")
        items = response.items
    } catch {
        notifications.add(.error("Failed to load items: \(error.localizedDescription)"))
    }
}
```

### Error Handling

- Python handlers should return `OperationResult` for mutations
- Swift should show user-friendly error messages
- Log technical details to stderr

### View Guidelines

- Prefer small, composable views
- Use `@Environment(AppState.self)` for state access
- Add accessibility identifiers for UI testing

```swift
struct ItemRow: View {
    let item: Item

    var body: some View {
        HStack {
            Text(item.name)
            Spacer()
            StatusBadge(status: item.status)
        }
        .accessibilityIdentifier("itemRow-\(item.id)")
    }
}
```

---

## Getting Help

- **Questions:** Open a GitHub Discussion
- **Bugs:** Open a GitHub Issue with reproduction steps
- **Feature requests:** Open a GitHub Issue with use case

---

## License

By contributing, you agree that your contributions will be licensed under the project's license.

---

Thank you for contributing to DevFlow!
