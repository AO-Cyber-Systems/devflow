# DevFlow - Task Tracking

## Current Sprint: Prerequisites Installation Feature

### Phase 1: Backend Foundation & Mise Integration

- [x] **1.1** Create `devflow/providers/installers/` module structure
  - [x] `__init__.py` - Module exports
  - [x] `base.py` - Abstract `InstallerBase` class
  - [x] `registry.py` - Tool registry with metadata
  - [x] `platform.py` - Platform detection utilities

- [x] **1.2** Implement platform detection
  - [x] Detect OS (Linux, macOS, Windows)
  - [x] Detect Linux distro (Ubuntu, Fedora, Arch)
  - [x] Detect WSL vs native Windows
  - [x] Detect available package managers (brew, apt, winget, snap)

- [x] **1.3** Implement Mise integration
  - [x] Add Mise detection (`mise --version`)
  - [x] Create Mise installer for all platforms
  - [x] Add runtime installation via Mise
  - [x] Support `mise use` for languages

- [x] **1.4** Create bridge handler
  - [x] `bridge/handlers/setup.py`
  - [x] RPC methods: `get_prerequisites`, `install`, `detect_tool`, etc.
  - [x] Register in `bridge/main.py`

### Phase 2: Tool Detection & Installers

- [x] **2.1** Code editor detection (in registry.py)
  - [x] VS Code (`code --version`)
  - [x] Zed (`zed --version`)
  - [x] Cursor (`cursor --version`)
  - [x] Windsurf detection
  - [x] Neovim (`nvim --version`)
  - [x] Helix (`hx --version`)

- [x] **2.2** Implement platform installers
  - [x] `installers/brew.py` - Homebrew (macOS/Linux)
  - [x] `installers/apt.py` - APT (Debian/Ubuntu)
  - [x] `installers/winget.py` - Windows Package Manager
  - [x] `installers/snap.py` - Snap packages
  - [x] `installers/mise.py` - Mise for language runtimes

- [x] **2.3** Create tool registry with installation methods
  - [x] Code editors (VS Code, Zed, Cursor, Windsurf, Neovim, Helix)
  - [x] Container tools (Docker)
  - [x] CLI tools (gh, op, supabase, mkcert, claude)
  - [x] Modern CLI utilities (ripgrep, fd, bat, eza, fzf, jq, yq, zoxide, delta, starship)

### Phase 3: UI Implementation

- [x] **3.1** Create Setup page (`ui/src/pages/Setup.tsx`)
  - [x] Tab navigation (Prerequisites, Authentication, Diagnostics)
  - [x] Prerequisites tab layout with categories
  - [x] Integration with existing Doctor checks

- [x] **3.2** Create Rust Tauri commands
  - [x] `ui/src-tauri/src/commands/setup.rs`
  - [x] Register commands in `lib.rs`

- [x] **3.3** Update navigation
  - [x] Replace Doctor with "Setup & Health" in sidebar
  - [x] Add `/setup` route to App.tsx
  - [x] Redirect `/doctor` to `/setup`

- [x] **3.4** Create API layer
  - [x] `ui/src/api/setup.ts` - Setup API calls
  - [x] Add types in `ui/src/types/index.ts`

### Phase 4: Integration & Testing

- [ ] **4.1** Connect UI to backend
  - [x] Wire up prerequisite detection
  - [x] Implement installation flow
  - [ ] Add progress streaming for installations
  - [ ] Handle errors gracefully with detailed messages

- [ ] **4.2** Add configuration
  - [ ] Default editor setting in GlobalConfig
  - [ ] Preferred package manager setting
  - [ ] Installed tools tracking

- [x] **4.3** Testing
  - [x] Unit tests for installers (111 tests: platform, registry, installers, setup handler)
  - [ ] Unit tests for UI components
  - [ ] E2E tests for installation flow

### Phase 5: Polish & Documentation

- [ ] **5.1** Advanced features
  - [ ] "Install All Missing" batch action
  - [ ] Export/import tool configurations
  - [ ] Authentication helpers (gh auth, op signin)
  - [ ] Installation modal with progress and logs

- [ ] **5.2** Documentation
  - [ ] Update README with prerequisites feature
  - [ ] Add user documentation for Setup page

---

## Discovered During Work

- Need to add progress streaming for async installations
- Consider adding installation method selection in the UI
- JetBrains Toolbox detection could be useful in the future
- Fixed attribute naming in setup handler: `tool.binary` (not `command`), `tool.is_essential` (not `essential`), `tool.managed_by_mise` (not `mise_managed`)
- ToolStatus doesn't have `installed_via` attribute - removed from detect_tool response

## TODO: CI/CD Improvements

- [ ] **Auto-publish releases**: Change `.github/workflows/build.yml` to publish releases automatically instead of creating drafts. Update the `softprops/action-gh-release` step to use `draft: false` instead of `draft: true`.

---

## Completed Tasks

### 2025-01-24

- Implemented Tauri auto-update release pipeline:
  - Added `tauri-plugin-updater` and `tauri-plugin-process` to Cargo.toml
  - Added `@tauri-apps/plugin-updater` and `@tauri-apps/plugin-process` to package.json
  - Configured updater plugin in `tauri.conf.json` with GitHub releases endpoint
  - Registered updater and process plugins in `lib.rs`
  - Created `ui/src/api/updater.ts` with checkForUpdates, installUpdate, downloadAndInstallUpdate
  - Updated `.github/workflows/build.yml` with:
    - TAURI_SIGNING_PRIVATE_KEY environment variable
    - Signature file (.sig) uploads for all platforms
    - latest.json generation for auto-updater
  - Added unit tests for updater API (9 tests)

- Created `devflow/providers/installers/` module with:
  - `platform.py` - Platform detection (OS, distro, architecture, WSL, package managers)
  - `base.py` - Abstract base classes (`InstallerBase`, `ToolDetector`, `ToolInfo`, etc.)
  - `registry.py` - Complete tool registry with 33 tools across 9 categories
  - `brew.py` - Homebrew installer
  - `apt.py` - APT installer
  - `mise.py` - Mise version manager installer
  - `winget.py` - Windows Package Manager installer
  - `snap.py` - Snap package installer
  - `__init__.py` - Module exports and factory functions

- Created `bridge/handlers/setup.py` with RPC methods:
  - `get_platform_info`, `get_categories`, `get_all_tools`, `get_essential_tools`
  - `detect_tool`, `detect_all_tools`, `detect_essential_tools`
  - `get_install_methods`, `install`, `install_multiple`
  - `check_mise_available`, `get_mise_installed_tools`
  - `get_prerequisites_summary`, `refresh_platform_info`

- Created `ui/src-tauri/src/commands/setup.rs` with Tauri commands

- Created `ui/src/api/setup.ts` TypeScript API layer

- Added setup types to `ui/src/types/index.ts`

- Created `ui/src/pages/Setup.tsx` with tabbed interface:
  - Prerequisites tab - Tool categories with install buttons
  - Authentication tab - Auth status and quick links
  - Diagnostics tab - Doctor checks (moved from Doctor page)

- Updated navigation to use "Setup & Health" instead of "Doctor"

---

## Notes

- Mise is the primary tool for managing language runtimes
- Zed now supports Windows (DirectX 11 backend)
- JetBrains Fleet is being discontinued (Dec 2025) - do not include
- Focus on cross-platform support (Linux, macOS, Windows/WSL2)
- AI-focused editors: VS Code, Cursor, Windsurf, Zed
- Docker only for containers (no Podman/Rancher in initial release)
- Full developer kit with modern CLI tools (ripgrep, fd, bat, etc.)
