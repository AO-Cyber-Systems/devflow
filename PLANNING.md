# DevFlow - Project Planning

## Overview

DevFlow is a hybrid desktop and CLI application for managing local development environments, database migrations, secrets management, and deployments across Docker-based infrastructure.

## Architecture

### Tech Stack

**Frontend (UI)**
- Framework: React 19 with TypeScript
- Desktop: Tauri 2 (cross-platform)
- Styling: Tailwind CSS 4
- State: Zustand
- Data Fetching: TanStack React Query
- Editor: Monaco Editor (for YAML config)

**Backend**
- Language: Python 3.10+
- CLI Framework: Typer
- RPC Server: Custom JSON-RPC over stdio
- Config: YAML with Pydantic validation

**Desktop Bridge (Rust)**
- Framework: Tauri 2
- Plugins: tauri-plugin-shell, tauri-plugin-log

### Communication Flow

```
Desktop UI (React/Tauri)
    ↓ Tauri Invoke Commands
Rust Sidecar (src-tauri/src)
    ↓ TCP/RPC
Python Bridge Server (bridge/main.py)
    ↓ RPC Handlers
Python CLI Backend (devflow/commands/*)
    ↓ System Calls
Docker/Git/1Password/SSH
```

## Current Features

- Multi-project management
- YAML configuration editing with validation
- Infrastructure status monitoring (Traefik)
- Development environment control (Docker Compose)
- System health checks ("Doctor" diagnostics)
- Project discovery and registration
- Cross-platform desktop delivery via Tauri

## Coding Standards

### Python
- Format with `black --line-length 120`
- Type hints required for function signatures
- Pydantic models for data validation
- Async support via asyncio

### TypeScript/React
- Strict TypeScript
- Functional components with hooks
- Zustand for global state
- TanStack Query for server state

### File Organization
- UI components in `ui/src/components/`
- Pages in `ui/src/pages/`
- API calls in `ui/src/api/`
- Python commands in `devflow/commands/`
- Bridge handlers in `bridge/handlers/`

## Current Work: Prerequisites Installation Feature

### Goal
Allow users to install development prerequisites directly from the DevFlow UI, including code editors (VS Code, Zed, Cursor), runtimes (via Mise), and CLI tools.

### Key Decisions

1. **Language/Runtime Management**: Use Mise as the polyglot version manager
2. **Code Editors**: AI-focused - VS Code, Cursor, Windsurf, Zed (covers modern AI-assisted development)
3. **Container Runtimes**: Docker Desktop only (simplifies initial release)
4. **UI Approach**: Rename Doctor to "Setup & Health" (`/setup`) with tabs (Prerequisites, Authentication, Diagnostics)
5. **CLI Tools**: Full developer kit including modern replacements (ripgrep, fd, bat, fzf, jq)
6. **Permissions**: Prompt with explanation before sudo commands
7. **Auto-detection**: Scan on startup, cache for session, manual refresh available
8. **Installation Progress**: Modal dialog with progress bar, logs, and cancel button

### Implementation Phases

1. **Phase 1**: Mise integration for runtime management
2. **Phase 2**: Code editor detection and installation
3. **Phase 3**: CLI tool categories and installers
4. **Phase 4**: UI components (Setup page, cards, modals)
5. **Phase 5**: Advanced features (batch install, config sync)

## Design Patterns

### Installer Architecture
- Abstract `InstallerBase` class
- Platform-specific implementations (brew, apt, winget, snap)
- Tool-specific installers inherit from base

### UI Component Patterns
- Cards for tool display with status badges
- Modals for installation progress
- Tabs for category organization
- Consistent dark theme styling

## Dependencies

### Required External Tools
- Docker (for infrastructure)
- Git (for version control)
- Mise (for language management - new)

### Optional External Tools
- 1Password CLI (secrets)
- Supabase CLI (database)
- mkcert (TLS certificates)
- GitHub CLI (GitHub operations)
