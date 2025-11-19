# PRD-014: DevFlow CLI

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)

---

## Executive Summary

The DevFlow CLI (`devflow`) is the unified command-line interface for the entire platform. It bridges the gap between local development and cloud deployment, managing everything from local Docker environments to production releases. It serves as the primary entry point for developers interacting with DevFlow Hub, Code, and Runtime.

---

## Goals

1. **Unified Experience**: Single binary for all products (`devflow`).
2. **Local Development**: One command (`devflow up`) to start the entire local stack.
3. **Automation**: Scriptable interface for CI/CD and scripts.
4. **Onboarding**: Interactive `devflow init` wizard for new projects.
5. **Sync**: Manage synchronization between local and remote environments.

---

## Command Structure

### Top-Level Commands

- `devflow init`: Initialize a new project
- `devflow auth`: Manage authentication
- `devflow up/down`: Manage local stack
- `devflow status`: Check system health
- `devflow config`: Manage configuration

### Product Namespaces

#### Hub (`devflow hub`)
- `devflow hub search`: Search knowledge base
- `devflow hub agent`: Spawn or attach to an agent
- `devflow hub task`: Create or list tasks
- `devflow hub sync`: Trigger integration sync

#### Code (`devflow code`)
- `devflow code pr`: Create/list pull requests
- `devflow code review`: Trigger AI review locally
- `devflow code publish`: Publish package to registry

#### Runtime (`devflow runtime`)
- `devflow runtime deploy`: Deploy application
- `devflow runtime logs`: Stream logs
- `devflow runtime env`: Manage environment variables
- `devflow runtime db`: Connect to database

#### Analytics (`devflow analytics`)
- `devflow analytics flag`: Toggle feature flags

---

## Architecture

- **Language**: Go (for performance and single binary distribution)
- **Distribution**: Homebrew, npm, apt, yum, chocolatey
- **Update Mechanism**: Self-update (`devflow update`)
- **Plugin System**: Support for external plugins (`devflow plugin install`)

---

## Local Stack Management

The CLI manages the local Docker Compose stack defined in PRD-008.

```bash
# Start local environment
devflow up

# Start specific services
devflow up --services hub,postgres

# Reset database
devflow db reset
```

---

## Interactive Mode

Most commands support an interactive TUI (Text User Interface) mode.

```bash
$ devflow init

? Project name: my-app
? Template: Next.js + Supabase
? Initialize git? Yes
? Deploy to: Local (Docker)

Creating project... Done!
Run 'cd my-app && devflow up' to start.
```

---

## Success Metrics

- **Installation Time**: < 1 minute
- **Startup Time**: < 500ms
- **Update Rate**: > 90% of users on latest version within 1 week

---

**End of PRD-014**
