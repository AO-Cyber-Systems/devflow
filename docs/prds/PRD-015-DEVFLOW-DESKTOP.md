# PRD-015: DevFlow Desktop

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)  
**Investment:** $100,000 over 6 months (Optional)

---

## Executive Summary

DevFlow Desktop is an optional native application providing a rich graphical interface for the local DevFlow environment. It bundles the CLI, manages the local Docker stack, and provides system tray notifications for agent activities. It is designed for developers who prefer GUI tools over command-line interfaces for environment management.

---

## Goals

1. **Simplified Setup**: One-click installer that sets up Docker, CLI, and dependencies.
2. **Stack Management**: Visual Start/Stop for local services with log viewing.
3. **Notifications**: Native system notifications for agent completion or Guardian alerts.
4. **Offline Mode**: First-class support for working without internet.

---

## Features

### 1. Stack Manager
- Visual dashboard for local containers
- One-click "Start DevFlow"
- Resource usage monitoring (CPU/RAM)
- Log viewer for specific services

### 2. Embedded Dashboard
- Wraps the Web UI (PRD-005) in a native window
- Adds native OS integrations (menu bar, shortcuts)

### 3. Agent Tray
- System tray icon showing active agent count
- Quick menu to pause/resume agents
- Notifications when tasks complete

### 4. Auto-Update
- Automatically updates CLI and Docker images
- Channel selection (Stable vs Edge)

---

## Architecture

- **Framework**: Electron + React
- **Bundling**: Includes `devflow` CLI binary
- **Communication**: Uses CLI for actual operations (`devflow up`, `devflow down`)
- **Update**: Electron Builder

---

## Investment

- **Cost**: $100k (6 months)
- **Priority**: Low (Optional / Phase 4)
- **Reasoning**: Enhances ease of use but not critical for core functionality. CLI is sufficient for MVP.

---

**End of PRD-015**
