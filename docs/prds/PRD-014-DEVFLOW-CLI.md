# PRD-014: DevFlow CLI

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)

---

## Executive Summary

The DevFlow CLI (`flow`) is the unified command-line interface for the entire platform. It bridges the gap between local development and cloud deployment, managing everything from local Docker environments to production releases. It serves as the primary entry point for developers interacting with DevFlow Hub, Code, and Runtime.

---

## Goals

1. **Unified Experience**: Single binary for all products (`flow`).
2. **Local Development**: One command (`flow up`) to start the entire local stack.
3. **Automation**: Scriptable interface for CI/CD and scripts.
4. **Onboarding**: Interactive `flow init` wizard for new projects.
5. **Sync**: Manage synchronization between local and remote environments.

---

## Command Structure

### Top-Level Commands

- `flow init`: Initialize a new project
- `flow auth`: Manage authentication
- `flow up/down`: Manage local stack
- `flow status`: Check system health
- `flow config`: Manage configuration

### Product Namespaces

#### Hub (`flow hub`)
- `flow hub search`: Search knowledge base
- `flow hub agent`: Spawn or attach to an agent
- `flow hub task`: Create or list tasks
- `flow hub sync`: Trigger integration sync

#### Code (`flow code`)
- `flow code pr`: Create/list pull requests
- `flow code review`: Trigger AI review locally
- `flow code publish`: Publish package to registry

#### Runtime (`flow runtime`)
- `flow runtime deploy`: Deploy application
- `flow runtime logs`: Stream logs
- `flow runtime env`: Manage environment variables
- `flow runtime db`: Connect to database

#### Analytics (`flow analytics`)
- `flow analytics flag`: Toggle feature flags

---

## Architecture

- **Language**: Go (for performance and single binary distribution)
- **Distribution**: Homebrew, npm, apt, yum, chocolatey
- **Update Mechanism**: Self-update (`flow update`)
- **Plugin System**: Support for external plugins (`flow plugin install`)

---

## Local Stack Management

The CLI manages the local Docker Compose stack defined in PRD-008.

```bash
# Start local environment
flow up

# Start specific services
flow up --services hub,postgres

# Reset database
flow db reset
```

---

## Interactive Mode

Most commands support an interactive TUI (Text User Interface) mode.

```bash
$ flow init

? Project name: my-app
? Template: Next.js + Supabase
? Initialize git? Yes
? Deploy to: Local (Docker)

Creating project... Done!
Run 'cd my-app && flow up' to start.
```

---

## Success Metrics

- **Installation Time**: < 1 minute
- **Startup Time**: < 500ms
- **Update Rate**: > 90% of users on latest version within 1 week

---

**End of PRD-014**
