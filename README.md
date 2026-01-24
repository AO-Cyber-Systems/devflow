# Devflow

A comprehensive CLI tool for managing local development environments, database migrations, secrets synchronization, and deployments.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Features

- **Local Development** - Unified setup with Docker Compose, shared Traefik infrastructure, and 1Password integration for environment templates
- **Database Migrations** - Apply, rollback, and track migrations with proper locking across local, staging, and production
- **Secrets Management** - Sync secrets from 1Password to GitHub Actions and Docker Swarm
- **Deployment** - Deploy to Docker Swarm clusters with rolling updates, health checks, and rollback support
- **Cross-Platform** - Native support for Linux, macOS, and Windows (via WSL2)

## Platform Support

| Platform | CLI | Desktop UI | Notes |
|----------|-----|------------|-------|
| Linux | ✅ | ✅ | Native support |
| macOS | ✅ | ✅ | Native support (Intel & Apple Silicon) |
| Windows | ✅ | ✅ | Requires WSL2 with Ubuntu |

**Windows Users**: DevFlow on Windows uses WSL2 for optimal Docker compatibility. See [Windows Setup Guide](docs/windows-setup.md) for installation instructions.

## Documentation

| Document | Description |
|----------|-------------|
| [Installation](docs/wiki/Installation.md) | Getting started with devflow |
| [Configuration](docs/wiki/Configuration.md) | `devflow.yml` reference |
| [Commands](docs/wiki/Commands.md) | Complete command reference |
| [Use Cases](docs/wiki/Use-Cases.md) | Common workflows and scenarios |
| [Providers](docs/wiki/Providers.md) | External tool integrations |
| [Windows Setup](docs/windows-setup.md) | Windows installation with WSL2 |

## Quick Start

```bash
# Install devflow
pip install devflow

# First-time setup (creates ~/.devflow/, configures git, installs Claude plugin)
devflow install

# Initialize in your project
cd your-project
devflow init

# Check system health
devflow doctor

# Set up local development
devflow dev setup

# Start services
devflow dev start
```

## Command Overview

### Local Development

```bash
devflow dev setup              # Set up local environment
devflow dev start              # Start services
devflow dev stop               # Stop services
devflow dev logs api --follow  # View logs
devflow dev shell api          # Shell into container
devflow dev reset --volumes    # Reset everything
```

### Database Operations

```bash
devflow db status              # Show migration status
devflow db migrate             # Apply pending migrations
devflow db migrate --dry-run   # Preview changes
devflow db create "add_users"  # Create new migration
devflow db rollback            # Rollback last migration
devflow db connect             # Open psql session
```

### Secrets Management

```bash
devflow secrets list                            # List secrets
devflow secrets sync --from 1password --to github  # Sync to GitHub
devflow secrets sync --from 1password --to docker  # Sync to Swarm
devflow secrets verify                          # Verify sync status
devflow secrets export --output .env.local      # Export for local dev
```

### Deployment

```bash
devflow deploy status          # Show deployment status
devflow deploy staging         # Deploy to staging
devflow deploy production      # Deploy to production
devflow deploy rollback        # Rollback deployment
devflow deploy logs api        # View service logs
devflow deploy ssh             # SSH to cluster node
```

### Shared Infrastructure

```bash
devflow infra up               # Start Traefik
devflow infra status           # Check status
devflow infra configure .      # Configure project
devflow infra doctor           # Health check
```

## Configuration

Create a `devflow.yml` in your project root:

```yaml
version: "1"

project:
  name: my-project

database:
  migrations:
    directory: supabase/migrations
    format: sql
  environments:
    local:
      url_env: DATABASE_URL
    staging:
      url_secret: app_database_url
      host: staging.example.com
      ssh_user: deploy

secrets:
  provider: 1password
  vault: Development
  mappings:
    - name: database_url
      op_item: "Database"
      op_field: connection_string
      github_secret: DATABASE_URL
      docker_secret: app_database_url

deployment:
  registry: ghcr.io
  organization: my-org
  services:
    api:
      image: myapp-api
      stack: myapp
  environments:
    staging:
      host: staging.example.com
      ssh_user: deploy

development:
  compose_file: docker-compose.yml
  services:
    - db
    - api

infrastructure:
  enabled: true
  network_name: devflow-proxy
```

See the [Configuration Reference](docs/wiki/Configuration.md) for all options.

## Requirements

### Required

- Python 3.10+
- Docker with Docker Compose v2
- Git

### Optional (based on features used)

| Tool | Purpose | Installation |
|------|---------|--------------|
| [1Password CLI](https://1password.com/downloads/command-line/) | Secrets management | `brew install 1password-cli` |
| [GitHub CLI](https://cli.github.com/) | GitHub integration | `brew install gh` |
| [mkcert](https://github.com/FiloSottile/mkcert) | Local HTTPS | `brew install mkcert` |
| [Supabase CLI](https://supabase.com/docs/guides/cli) | Supabase migrations | `brew install supabase/tap/supabase` |
| [PostgreSQL](https://www.postgresql.org/) | Database connections | `brew install postgresql` |

Run `devflow doctor` to check installation status.

## Development

```bash
# Clone the repository
git clone https://github.com/AO-Cyber-Systems/devflow.git
cd devflow

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black devflow tests
ruff check devflow tests
mypy devflow
```

## License

MIT
