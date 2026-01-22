# Devflow Documentation

**Devflow** is a comprehensive CLI tool for managing local development environments, database migrations, secrets synchronization, and deployments. It provides a unified interface for common development operations across projects.

## Documentation Index

| Document | Description |
|----------|-------------|
| [Installation](Installation.md) | Getting started with devflow |
| [Configuration](Configuration.md) | `devflow.yml` reference |
| [Commands](Commands.md) | Complete command reference |
| [Use Cases](Use-Cases.md) | Common workflows and scenarios |
| [Providers](Providers.md) | External tool integrations |

## Feature Overview

### Local Development
- **Unified setup** - Single command to configure your development environment
- **Docker Compose integration** - Manage services with familiar compose files
- **Shared infrastructure** - Traefik proxy with automatic HTTPS for all projects
- **Environment templates** - 1Password integration for `.env` file generation

### Database Management
- **Migration tracking** - Apply, rollback, and track database migrations
- **Multiple executors** - SQL or Supabase CLI based execution
- **Environment support** - Local, staging, and production environments
- **Safety features** - Advisory locking, dry-run mode, confirmation prompts

### Secrets Management
- **1Password integration** - Read secrets from your vault
- **GitHub Actions sync** - Automatically sync secrets to GitHub
- **Docker Swarm sync** - Sync to Docker Swarm secrets
- **Verification** - Verify secrets are in sync across systems

### Deployment
- **Docker Swarm** - Deploy to Swarm clusters via SSH
- **Rolling updates** - Zero-downtime deployments
- **Rollback support** - Quick rollback to previous versions
- **Multi-environment** - Staging and production with different approval workflows

## Architecture

```
devflow/
├── cli.py              # Main CLI entry point
├── commands/           # Command implementations
│   ├── config.py       # Configuration commands
│   ├── db.py           # Database/migration commands
│   ├── deploy.py       # Deployment commands
│   ├── dev.py          # Local development commands
│   ├── infra.py        # Infrastructure commands
│   └── secrets.py      # Secrets management commands
├── core/
│   └── config.py       # Configuration loading and validation
├── infrastructure/     # Shared infrastructure management
├── migrations/         # Migration engine and executors
└── providers/          # External tool integrations
```

## Requirements

- **Python 3.10+**
- **Docker** with Docker Compose
- **Git**

### Optional Dependencies

| Tool | Purpose | Installation |
|------|---------|--------------|
| [1Password CLI](https://1password.com/downloads/command-line/) | Secrets management | `brew install 1password-cli` |
| [GitHub CLI](https://cli.github.com/) | GitHub integration | `brew install gh` |
| [mkcert](https://github.com/FiloSottile/mkcert) | Local HTTPS certificates | `brew install mkcert` |
| [Supabase CLI](https://supabase.com/docs/guides/cli) | Supabase migrations | `brew install supabase/tap/supabase` |
| [PostgreSQL](https://www.postgresql.org/) | Database connections | `brew install postgresql` |

## Getting Started

```bash
# Install devflow
pip install devflow

# Initialize a new project
devflow init

# Check system health
devflow doctor

# Set up local development
devflow dev setup

# Start services
devflow dev start
```

## Support

- [GitHub Issues](https://github.com/AO-Cyber-Systems/devflow/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/AO-Cyber-Systems/devflow/discussions) - Questions and community discussion
