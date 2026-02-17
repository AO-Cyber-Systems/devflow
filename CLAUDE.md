# DevFlow - Claude Code Guide

## Project Structure

- `ui-native/` - SwiftUI macOS application
- `bridge/` - Python JSON-RPC bridge server
- `devflow/` - Python core library
- `tests/` - Test suites

## Building & Running

### Quick Build (swift build)
```bash
cd ui-native && swift build
.build/debug/DevFlow
```
Note: Apps built this way have limited accessibility support for UI automation.

### Xcode Build (recommended for UI automation)
```bash
cd ui-native

# Build the app
xcodebuild -scheme DevFlow -configuration Debug -derivedDataPath .build/xcode build

# Run the built app
open .build/xcode/Build/Products/Debug/DevFlow.app

# Or run directly
.build/xcode/Build/Products/Debug/DevFlow.app/Contents/MacOS/DevFlow
```

### One-liner: Build and Run
```bash
cd ui-native && xcodebuild -scheme DevFlow -configuration Debug -derivedDataPath .build/xcode build && open .build/xcode/Build/Products/Debug/DevFlow.app
```

### Run Python bridge directly (for testing RPC)
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"system.ping","params":{}}' | python -m bridge.main
```

## Contract Tests

When fixing JSON decoding errors between Swift and Python:

```bash
# Generate response snapshots from Python
python tests/contracts/generate_snapshots.py

# Run Swift contract tests
cd ui-native && swift test --filter ContractTests
```

## XCUITests

Comprehensive UI tests for the DevFlow macOS app. Use these to verify UI functionality.

### When to Use

- **After making UI changes**: Run to verify navigation and elements still work
- **Before releases**: Full test suite ensures all features accessible
- **After Swift model changes**: Verify data binding and display
- **When debugging UI issues**: Isolate which component is failing

### Running Tests

```bash
cd ui-native

# Run all UI tests
xcodebuild test -scheme DevFlow -destination 'platform=macOS'

# Run specific test class
xcodebuild test -scheme DevFlow -destination 'platform=macOS' -only-testing:DevFlowUITests/DevFlowUITests

# Run specific test method
xcodebuild test -scheme DevFlow -destination 'platform=macOS' -only-testing:DevFlowUITests/DevFlowUITests/testDashboardLoads
```

### Test Coverage

The test suite covers:

| Section | Tests | Key Identifiers |
|---------|-------|-----------------|
| **Navigation** | Sidebar nav, keyboard shortcuts | `navDashboard`, `navProjects`, etc. |
| **Dashboard** | Load, refresh, status cards | `dashboardView`, `refreshDashboardButton` |
| **Infrastructure** | View load, toggle buttons | `infrastructureView`, `toggleAllInfraButton` |
| **Projects** | List, add sheet, search | `addProjectButton`, `projectSearchField` |
| **Secrets** | List, add sheet | `addSecretButton`, `secretKeyField` |
| **Settings** | Config fields | `baseDomainField`, `traefikPortField` |
| **Tools** | Browser, filters, search | `toolBrowserView`, `toolSearchField` |
| **Templates** | Browser view | `templateBrowser` |
| **Logs** | Viewer, filters, auto-scroll | `logViewerView`, `logLevelFilter` |
| **AI Agents** | Browser, search, filters | `agentBrowserView`, `agentSearchField` |
| **Documentation** | View, search, add | `docsView`, `docsSearchField`, `addDocButton` |
| **Code Search** | View, search, scan | `codeSearchView`, `codeSearchField` |
| **Databases** | View, add sheet | `databaseView`, `addDatabaseButton` |
| **Command Palette** | Open/close, search | `commandPaletteView`, `commandSearchField` |

### Adding New Tests

1. Add accessibility identifier to view:
   ```swift
   .accessibilityIdentifier("myNewView")
   ```

2. Add test method in `DevFlowUITests.swift`:
   ```swift
   func testMyNewViewLoads() throws {
       XCTAssertTrue(button("navMySection").waitForExistence(timeout: 3))
       button("navMySection").tap()
       XCTAssertTrue(element("myNewView").waitForExistence(timeout: 5))
   }
   ```

3. Run test:
   ```bash
   xcodebuild test -scheme DevFlow -destination 'platform=macOS' \
     -only-testing:DevFlowUITests/DevFlowUITests/testMyNewViewLoads
   ```

### Troubleshooting

- **Test can't find element**: Check accessibility identifier is set on the view
- **Element not hittable**: View may be obscured; check for sheets/overlays
- **Timeout failures**: Increase timeout or add `sleep(1)` for animations
- **App not launching**: Ensure no other DevFlow instance is running

## UI Automation

SwiftUI apps have limited compatibility with MCP UI automation tools. Use the AppleScript-based helper script instead.

### AppleScript Helper (Recommended)

The `ui-automation.sh` script provides reliable UI automation for SwiftUI apps:

```bash
cd ui-native

# Check app status
./scripts/ui-automation.sh status

# Get all text content (verify what's displayed)
./scripts/ui-automation.sh get-text

# List all UI elements
./scripts/ui-automation.sh list-elements

# List buttons
./scripts/ui-automation.sh list-buttons

# Click a button by name
./scripts/ui-automation.sh click-button "Fix Issues"

# Click menu item
./scripts/ui-automation.sh click-menu "DevFlow" "Quit DevFlow"

# Select sidebar item
./scripts/ui-automation.sh sidebar-select "Projects"

# Take screenshot
./scripts/ui-automation.sh screenshot /tmp/devflow-screenshot.png

# Launch app (if not running)
./scripts/ui-automation.sh launch
```

### Testing Workflows

1. **Verify app is running**:
   ```bash
   ./scripts/ui-automation.sh status
   # Expected: Running - 1 window(s), active: Dashboard
   ```

2. **Check current state** (get visible text):
   ```bash
   ./scripts/ui-automation.sh get-text
   ```

3. **Interact with UI**:
   ```bash
   ./scripts/ui-automation.sh click-button "Fix Issues"
   ```

4. **Verify result**:
   ```bash
   ./scripts/ui-automation.sh get-text | grep -i "installing"
   ```

### MCP Tools (Limited)

The MCP UI automation tools (`mcp__macos-ui-automation__*`) have known issues with SwiftUI apps:
- App may not appear in `list_running_applications` with correct name
- `find_elements_in_app` often returns empty results
- Window count may show as 0 even when windows are visible

If you need to use MCP tools, try:
```
mcp__macos-ui-automation__click_at_position
  x: 150
  y: 100
```

For reliable automation, prefer the AppleScript helper or coordinate-based clicking.

## Common Tasks

### Testing RPC Response Decoding

If Swift fails to decode a Python response:

1. Get the actual Python response:
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"system.full_doctor","params":{}}' | python -m bridge.main | python -m json.tool
   ```

2. Compare with Swift model in `ui-native/DevFlow/Models/`

3. Fix mismatches (common issues):
   - Snake_case vs camelCase (`CodingKeys`)
   - Optional vs required fields
   - Type mismatches (Int vs Double, String vs Bool)

### Adding New RPC Methods

1. Add Python handler in `bridge/handlers/`
2. Add Swift response model in `ui-native/DevFlow/Models/`
3. Add to contract tests in `tests/contracts/generate_snapshots.py`
4. Run contract tests to verify

### Debugging Connection Issues

```bash
# Check if Python bridge starts
python -c "from bridge.handlers.system import SystemHandler; print('OK')"

# Check installed package location
python -c "import bridge; print(bridge.__file__)"

# Reinstall in editable mode if needed
pip install -e /Users/justin/dev/devflow
```
