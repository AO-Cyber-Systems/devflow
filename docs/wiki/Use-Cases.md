# Use Cases & Workflows

Common workflows and scenarios for using devflow.

## Table of Contents

- [Local Development Setup](#local-development-setup)
- [Database Migrations](#database-migrations)
- [Secrets Management](#secrets-management)
- [Deployment Workflow](#deployment-workflow)
- [Multi-Project Setup](#multi-project-setup)
- [CI/CD Integration](#cicd-integration)

---

## Local Development Setup

### First-Time Project Setup

When joining a project or setting up a new development machine:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/your-project.git
cd your-project

# 2. Run devflow setup
devflow dev setup
```

The setup command:
1. Verifies Docker is running
2. Pulls required Docker images
3. Creates `.env.local` from `.env.template` (resolving 1Password references)
4. Starts shared infrastructure (Traefik) if configured

### Daily Development

```bash
# Start services
devflow dev start

# View logs
devflow dev logs api --follow

# Open shell in container
devflow dev shell api

# Stop services
devflow dev stop
```

### Environment Templates with 1Password

Create a `.env.template` file with 1Password references:

```bash
# .env.template
DATABASE_URL=op://Development/Database/connection_string
API_KEY=op://Development/API Keys/main_key
SECRET_KEY=op://Development/App Secrets/secret_key

# Non-secret values
DEBUG=true
LOG_LEVEL=debug
```

When you run `devflow dev setup`, it resolves the `op://` references:

```bash
# .env.local (generated)
DATABASE_URL=postgresql://user:pass@localhost:5432/myapp
API_KEY=sk-1234567890
SECRET_KEY=super-secret-key
DEBUG=true
LOG_LEVEL=debug
```

### Resetting Development Environment

When things go wrong or you need a fresh start:

```bash
# Reset containers (keeps data)
devflow dev reset

# Reset everything including database
devflow dev reset --volumes
```

---

## Database Migrations

### Creating Migrations

```bash
# Create a new migration
devflow db create add_user_preferences

# Creates: supabase/migrations/20240115120000_add_user_preferences.sql
```

Edit the generated file:

```sql
-- supabase/migrations/20240115120000_add_user_preferences.sql

CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    theme VARCHAR(20) DEFAULT 'light',
    notifications_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

For rollback support, create a corresponding down file:

```sql
-- supabase/migrations/20240115120000_add_user_preferences.down.sql

DROP TABLE IF EXISTS user_preferences;
```

### Applying Migrations

```bash
# Check status
devflow db status

# Apply to local
devflow db migrate

# Preview changes (dry run)
devflow db migrate --dry-run

# Apply to staging
devflow db migrate --env staging

# Apply to production (requires confirmation)
devflow db migrate --env production
```

### Rolling Back

```bash
# Rollback last migration
devflow db rollback

# Rollback multiple migrations
devflow db rollback --steps 3

# Preview rollback
devflow db rollback --dry-run

# Production rollback (requires --force)
devflow db rollback --env production --force
```

### Migration Best Practices

1. **Always create down migrations** for rollback support
2. **Use transactions** for data safety
3. **Test locally first** before applying to staging
4. **Use dry-run** to preview changes
5. **Keep migrations small** and focused

---

## Secrets Management

### Listing Secrets

```bash
# List from 1Password
devflow secrets list --source 1password

# List GitHub Actions secrets
devflow secrets list --source github

# List Docker Swarm secrets
devflow secrets list --source docker
```

### Syncing Secrets

Sync secrets from 1Password to other systems:

```bash
# Sync to GitHub Actions (preview first)
devflow secrets sync --from 1password --to github --dry-run

# Sync to GitHub Actions
devflow secrets sync --from 1password --to github

# Sync to Docker Swarm
devflow secrets sync --from 1password --to docker
```

### Verifying Sync Status

```bash
devflow secrets verify
```

Output:
```
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┓
┃ Secret         ┃ 1Password  ┃ GitHub ┃ Docker ┃ Status    ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━┩
│ database_url   │ ✓          │ ✓      │ ✓      │ in_sync   │
│ api_key        │ ✓          │ ✓      │ -      │ in_sync   │
│ jwt_secret     │ ✓          │ ✗      │ ✓      │ partial   │
└────────────────┴────────────┴────────┴────────┴───────────┘
```

### Exporting for Local Development

```bash
# Export to stdout
devflow secrets export

# Export to file
devflow secrets export --output .env.local
```

### Secrets Workflow

```
┌──────────────┐
│  1Password   │ ◄── Single source of truth
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│         devflow secrets sync          │
└──────┬───────────────┬───────────────┘
       │               │
       ▼               ▼
┌──────────────┐ ┌──────────────┐
│GitHub Actions│ │Docker Swarm  │
│   Secrets    │ │   Secrets    │
└──────────────┘ └──────────────┘
```

---

## Deployment Workflow

### Deployment Overview

```
┌─────────┐    ┌─────────┐    ┌────────────┐
│  Code   │───►│ Staging │───►│ Production │
│  Push   │    │ Deploy  │    │   Deploy   │
└─────────┘    └─────────┘    └────────────┘
                   │                │
                   ▼                ▼
              No approval     Requires approval
```

### Staging Deployment

```bash
# Check current status
devflow deploy status --env staging

# Deploy all services
devflow deploy staging

# Deploy with migrations
devflow deploy staging --migrate

# Deploy specific service
devflow deploy staging --service api

# Preview deployment
devflow deploy staging --dry-run
```

### Production Deployment

```bash
# Check status
devflow deploy status --env production

# Deploy (will prompt for confirmation)
devflow deploy production

# Skip confirmation
devflow deploy production --yes

# With migrations
devflow deploy production --migrate --yes
```

### Viewing Logs

```bash
# View recent logs
devflow deploy logs api --env staging

# Follow logs in real-time
devflow deploy logs api --env staging --follow

# Last 200 lines
devflow deploy logs api --env staging --tail 200
```

### Rolling Back

```bash
# Rollback all services in staging
devflow deploy rollback --env staging

# Rollback specific service
devflow deploy rollback --env staging --service api
```

### SSH to Cluster

```bash
# SSH to staging manager
devflow deploy ssh --env staging

# SSH to production worker
devflow deploy ssh --env production --node worker1
```

---

## Multi-Project Setup

### Shared Infrastructure

When working on multiple projects, use shared Traefik:

```bash
# Start shared infrastructure
devflow infra up

# Check status
devflow infra status
```

### Configuring Projects

```bash
# Configure project to use shared infra
devflow infra configure /path/to/project

# Preview changes
devflow infra configure /path/to/project --dry-run
```

This transforms the project's `docker-compose.yml`:
- Replaces project networks with `devflow-proxy`
- Removes embedded Traefik services
- Registers project domains

### Managing Multiple Projects

```bash
# Check registered projects
devflow infra status
```

Output:
```
Registered Projects
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Project                     ┃ Domains                       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ /home/user/projects/app1    │ app1.localhost, api.localhost │
│ /home/user/projects/app2    │ app2.localhost                │
└─────────────────────────────┴───────────────────────────────┘
```

### Restoring Original Config

```bash
devflow infra unconfigure /path/to/project
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install devflow
        run: pip install devflow

      - name: Run migrations
        run: devflow db migrate --env staging --ci
        env:
          DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}

      - name: Deploy to staging
        run: devflow deploy staging --yes --json
        env:
          SSH_PRIVATE_KEY: ${{ secrets.DEPLOY_SSH_KEY }}

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production  # Requires approval
    steps:
      - uses: actions/checkout@v4

      - name: Install devflow
        run: pip install devflow

      - name: Deploy to production
        run: devflow deploy production --yes --json
        env:
          SSH_PRIVATE_KEY: ${{ secrets.DEPLOY_SSH_KEY }}
```

### JSON Output for CI

All commands support `--json` for machine-readable output:

```bash
devflow db migrate --env staging --ci --json
```

Output:
```json
{
  "success": true,
  "applied": 2,
  "skipped": 0,
  "errors": [],
  "migrations": [
    {"name": "20240115_add_users", "status": "applied"},
    {"name": "20240116_add_posts", "status": "applied"}
  ]
}
```

### Syncing Secrets in CI

```bash
# Sync secrets before deployment
devflow secrets sync --from 1password --to docker --json
```

---

## Troubleshooting

### Common Issues

**Docker not running:**
```bash
devflow doctor --fix
```

**Database connection failed:**
```bash
# Check connectivity
devflow db connect --env local

# Verify environment
devflow config env
```

**Secrets not found:**
```bash
# Verify 1Password authentication
op whoami

# List available items
devflow secrets list --source 1password
```

**Migration conflicts:**
```bash
# Check status
devflow db status --env staging

# View pending migrations
devflow db status --json | jq '.pending'
```

### Getting Help

```bash
# General help
devflow --help

# Command-specific help
devflow db --help
devflow db migrate --help
```
