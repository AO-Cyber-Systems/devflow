# DevFlow Native macOS App

Native SwiftUI macOS application for DevFlow, replacing the Tauri/SvelteKit implementation.

## Requirements

- macOS 14.0 (Sonoma) or later
- Xcode 16.0 or later
- Swift 6.0+
- Python 3 (for backend)

## Building

### Using Xcode

```bash
cd ui-native
open DevFlow.xcodeproj
# Press Cmd+R to build and run
```

### Using Command Line

```bash
cd ui-native
xcodebuild -project DevFlow.xcodeproj -scheme DevFlow -configuration Debug build
```

## Testing

### Unit Tests

```bash
xcodebuild test -project DevFlow.xcodeproj -scheme DevFlow -destination 'platform=macOS'
```

### UI Tests with XCUITest

```bash
xcodebuild test -project DevFlow.xcodeproj -scheme DevFlow -destination 'platform=macOS' -only-testing:DevFlowUITests
```

### AI Testing with macos-ui-automation MCP

All interactive UI elements have accessibility identifiers for AI-driven testing:

```
# Find all buttons in DevFlow
mcp__macos-ui-automation__find_elements_in_app with app_name="DevFlow"

# Click the Start Infrastructure button
mcp__macos-ui-automation__click_element_by_selector with jsonpath_selector="$..[?(@.ax_identifier=='toggleInfraButton')]"

# Verify infrastructure status shows Running
mcp__macos-ui-automation__find_elements with jsonpath_selector="$..[?(@.ax_identifier=='statusBadgeRunning')]"
```

## Project Structure

```
ui-native/
├── DevFlow.xcodeproj          # Xcode project
├── DevFlow/
│   ├── DevFlowApp.swift       # @main entry point
│   ├── ContentView.swift      # Main navigation
│   ├── Models/                # Data models
│   ├── State/                 # @Observable AppState
│   ├── Services/              # PythonBridge, RpcClient
│   ├── Views/                 # SwiftUI views
│   │   ├── Dashboard/
│   │   ├── Infrastructure/
│   │   ├── Projects/
│   │   ├── Secrets/
│   │   ├── Config/
│   │   └── Components/
│   └── Resources/             # Assets, Info.plist
├── DevFlowTests/              # Unit tests
└── DevFlowUITests/            # XCUITest
```

## Architecture

The app uses:
- **SwiftUI** for the UI layer
- **@Observable** for state management
- **JSON-RPC over stdin/stdout** to communicate with the Python backend
- **Accessibility identifiers** on all interactive elements for AI testing

## Key Accessibility Identifiers

| Identifier | Element |
|------------|---------|
| `navDashboard` | Dashboard sidebar button |
| `navInfrastructure` | Infrastructure sidebar button |
| `navProjects` | Projects sidebar button |
| `navSecrets` | Secrets sidebar button |
| `navConfig` | Settings sidebar button |
| `toggleInfraButton` | Start/Stop all infrastructure |
| `addProjectButton` | Add project button |
| `addSecretButton` | Add secret button |
| `connectionStatus` | Backend connection indicator |

## Dependencies

- [swift-subprocess](https://github.com/swiftlang/swift-subprocess) - For process management (fetched via SPM)
