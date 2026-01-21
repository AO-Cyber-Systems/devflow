# Devflow

Developer workflow CLI for the AOCyber ecosystem.

## Overview

Devflow unifies and simplifies operations across AOCyber projects. It wraps and orchestrates GitHub CLI, 1Password CLI, Docker, and Supabase CLI to provide a consistent interface for:

- **Database migrations** with proper locking and tracking
- **Secrets management** from 1Password to GitHub to Docker Swarm
- **Deployment operations** with health checks and rollback support
- **Local development** environment setup and management

## Installation

```bash
# Clone the repository
git clone https://github.com/AO-Cyber-Systems/devflow.git ~/.devflow

# Install in development mode
cd ~/.devflow
pip install -e .

# Verify installation
devflow doctor
```

## Quick Start

```bash
# Initialize devflow in your project
cd your-project
devflow init --preset aocodex

# Check system health
devflow doctor

# Check migration status
devflow db status

# Apply pending migrations
devflow db migrate --env staging

# Deploy to staging
devflow deploy staging
```

## Commands

### Database Operations

```bash
devflow db status                    # Show migration status
devflow db status --env staging      # Check staging database
devflow db migrate                   # Apply pending migrations
devflow db migrate --dry-run         # Preview migrations
devflow db create "add_user_prefs"   # Create new migration file
devflow db connect --env staging     # Open psql session
```

### Secrets Management

```bash
devflow secrets list                 # List configured secrets
devflow secrets sync --from 1password --to github
devflow secrets sync --from 1password --to docker
devflow secrets verify               # Check secrets are in sync
```

### Deployment

```bash
devflow deploy status                # Show deployment status
devflow deploy staging               # Deploy to staging
devflow deploy staging --migrate     # Deploy with migrations
devflow deploy production            # Deploy to production (requires confirmation)
devflow deploy rollback              # Rollback to previous version
devflow deploy logs backend          # View service logs
```

### Local Development

```bash
devflow dev setup                    # Set up local environment
devflow dev start                    # Start local services
devflow dev stop                     # Stop local services
devflow dev logs backend             # View local logs
devflow dev shell backend            # Shell into container
devflow dev reset --volumes          # Reset everything
```

## Configuration

Create a `devflow.yml` in your project root:

```yaml
version: "1"

project:
  name: my-project
  preset: aocodex  # Optional: use built-in preset

database:
  migrations:
    directory: supabase/migrations
    format: sql
    tracking_table: schema_migrations

  environments:
    local:
      url_env: DATABASE_URL
    staging:
      url_secret: my_project_database_url
      host: staging-server
      ssh_user: deploy

secrets:
  provider: 1password
  vault: MyVault
  mappings:
    - name: database_url
      op_item: "My Project Database"
      op_field: connection_string
      github_secret: DATABASE_URL
      docker_secret: my_project_database_url

deployment:
  registry: ghcr.io
  organization: my-org
  services:
    backend:
      image: my-project-backend
      stack: myproject
      health_endpoint: /health

development:
  compose_file: docker-compose.yml
  services:
    - db
    - backend
```

## Built-in Presets

Devflow includes presets for AOCyber projects:

- `aocodex` - AOCodex AI coding assistant
- `aosentry` - AOSentry AI gateway

Use with: `devflow init --preset aocodex`

## Requirements

Devflow wraps these tools (install them first):

- **gh** - GitHub CLI ([install](https://cli.github.com/))
- **op** - 1Password CLI ([install](https://1password.com/downloads/command-line/))
- **docker** - Docker Engine ([install](https://docs.docker.com/get-docker/))
- **supabase** - Supabase CLI ([install](https://supabase.com/docs/guides/cli))
- **psql** - PostgreSQL client

Run `devflow doctor` to check installation status.

## Development

```bash
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
