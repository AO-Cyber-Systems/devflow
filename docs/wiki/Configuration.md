# Configuration Reference

Devflow uses two levels of configuration:

1. **Global configuration** (`~/.devflow/config.yml`) - User-wide settings applied to all projects
2. **Project configuration** (`devflow.yml`) - Per-project settings in your project root

## Global Configuration

Created during `devflow install`, the global config stores user preferences:

```yaml
# ~/.devflow/config.yml
version: "1"

git:
  user_name: "Your Name"
  user_email: "your@email.com"
  co_author_enabled: true
  co_author_name: "Claude"
  co_author_email: "noreply@anthropic.com"

defaults:
  secrets_provider: 1password   # Default for new projects
  network_name: devflow-proxy
  registry: ghcr.io

infrastructure:
  auto_start: false
  traefik_http_port: 80
  traefik_https_port: 443
  traefik_dashboard_port: 8088

setup_completed: true
```

### Global Settings Reference

| Setting | Description | Default |
|---------|-------------|---------|
| `git.user_name` | Git user name | Detected from git |
| `git.user_email` | Git user email | Detected from git |
| `git.co_author_enabled` | Add Claude co-author to commits | `true` |
| `git.co_author_name` | Co-author name | `Claude` |
| `git.co_author_email` | Co-author email | `noreply@anthropic.com` |
| `defaults.secrets_provider` | Default secrets provider for new projects | `null` |
| `defaults.network_name` | Docker network for shared infrastructure | `devflow-proxy` |
| `defaults.registry` | Default container registry | `null` |
| `infrastructure.auto_start` | Auto-start Traefik with devflow commands | `false` |
| `infrastructure.traefik_http_port` | HTTP port | `80` |
| `infrastructure.traefik_https_port` | HTTPS port | `443` |
| `infrastructure.traefik_dashboard_port` | Dashboard port | `8088` |

---

## Project Configuration

Create `devflow.yml` in your project root with `devflow init`:

### Quick Start

```yaml
version: "1"

project:
  name: my-project

database:
  migrations:
    directory: migrations
    format: sql

development:
  compose_file: docker-compose.yml
```

### Complete Schema

```yaml
version: "1"           # Configuration version (required)
project: {...}         # Project metadata (required)
database: {...}        # Database configuration
secrets: {...}         # Secrets configuration
deployment: {...}      # Deployment configuration
development: {...}     # Local development configuration
infrastructure: {...}  # Shared infrastructure configuration
git: {...}             # Git configuration (project-level overrides)
```

---

## `project`

Project metadata and identification.

```yaml
project:
  name: string              # Project name (required)
  preset: string            # Optional preset (aocodex, aosentry)
```

### Example

```yaml
project:
  name: my-awesome-app
```

---

## `database`

Database connection and migration settings.

### `database.migrations`

```yaml
database:
  migrations:
    directory: string           # Path to migration files
                                # Default: supabase/migrations

    format: string              # Migration format
                                # Options: sql, supabase, prisma, alembic
                                # Default: sql

    tracking_table: string      # Table to track applied migrations
                                # Default: schema_migrations

    tracking_schema: string     # Schema for tracking table
                                # Default: public

    use_supabase_cli: bool      # Force Supabase CLI executor
                                # Default: false
```

### `database.environments`

Configure database connections per environment:

```yaml
database:
  environments:
    local:
      url_env: string           # Environment variable with DB URL
      direct_port: int          # Direct port for local access

    staging:
      url_secret: string        # Docker secret name for DB URL
      host: string              # SSH host for remote operations
      ssh_user: string          # SSH username

    production:
      url_secret: string        # Docker secret name for DB URL
      host: string              # SSH host
      ssh_user: string          # SSH username
      require_approval: bool    # Require confirmation for operations
                                # Default: false
```

### Complete Example

```yaml
database:
  migrations:
    directory: supabase/migrations
    format: sql
    tracking_table: schema_migrations

  environments:
    local:
      url_env: DATABASE_URL
      direct_port: 5432

    staging:
      url_secret: app_database_url
      host: staging-manager.example.com
      ssh_user: deploy

    production:
      url_secret: app_database_url
      host: prod-manager.example.com
      ssh_user: deploy
      require_approval: true
```

---

## `secrets`

Secrets management and synchronization.

```yaml
secrets:
  provider: string          # Secrets provider
                            # Options: 1password, env
                            # Default: null (uses global default)

  vault: string             # 1Password vault name

  github:                   # GitHub authentication settings
    auth: string            # Auth method: "cli" (default) or "app"
    app:                    # Required if auth: "app"
      app_id: string        # GitHub App ID
      installation_id: string  # Installation ID for your org
      private_key: string   # PEM private key (or op:// reference)

  mappings:                 # List of secret mappings
    - name: string                    # Secret identifier (required)
      op_item: string                 # 1Password item name
      op_field: string                # 1Password field name
      github_secret: string           # GitHub Actions secret name
      docker_secret: string           # Docker Swarm secret name
```

### Basic Example

```yaml
secrets:
  provider: 1password
  vault: Development

  mappings:
    - name: database_url
      op_item: "Database Credentials"
      op_field: connection_string
      github_secret: DATABASE_URL
      docker_secret: app_database_url

    - name: api_key
      op_item: "External APIs"
      op_field: stripe_key
      github_secret: STRIPE_API_KEY

    - name: jwt_secret
      op_item: "App Secrets"
      op_field: jwt_signing_key
      github_secret: JWT_SECRET
      docker_secret: jwt_secret
```

### GitHub App Authentication

For better security and auditability, you can use a GitHub App instead of personal access tokens. This is recommended for CI/CD and multi-repo secret sync.

**Benefits of GitHub App:**
- Not tied to a personal account
- Fine-grained per-repository permissions
- Higher rate limits (15,000/hour vs 5,000/hour)
- Automatic token rotation (JWT expires in 10 min)
- Shows as App in audit logs

**Configuration:**

```yaml
secrets:
  provider: 1password
  vault: AOCyber-Infrastructure

  github:
    auth: app
    app:
      # Direct values
      app_id: "12345"
      installation_id: "67890"
      private_key: |
        -----BEGIN RSA PRIVATE KEY-----
        ...
        -----END RSA PRIVATE KEY-----

      # Or use 1Password references (recommended)
      app_id: op://AOCyber-Infrastructure/GitHub-App/app_id
      installation_id: op://AOCyber-Infrastructure/GitHub-App/installation_id
      private_key: op://AOCyber-Infrastructure/GitHub-App/private_key

  mappings:
    - name: database_url
      op_item: "Database"
      op_field: url
      github_secret: DATABASE_URL
```

**Setup Steps:**

1. Create a GitHub App in your org settings
2. Configure permissions: `secrets: write`, `metadata: read`
3. Install the App on target repositories
4. Generate and download the private key
5. Store App ID, Installation ID, and private key in 1Password
6. Configure `secrets.github.app` in devflow.yml

**Usage:**

```bash
# Uses GitHub App if configured (auto mode)
devflow secrets sync --to github

# Force GitHub App
devflow secrets sync --to github --auth app

# Force gh CLI (ignores app config)
devflow secrets sync --to github --auth cli
```

---

## `deployment`

Docker Swarm deployment configuration.

### `deployment` Root

```yaml
deployment:
  registry: string          # Docker registry URL
                            # Default: ghcr.io

  organization: string      # Registry organization/namespace
```

### `deployment.services`

Define deployable services:

```yaml
deployment:
  services:
    service_name:
      image: string             # Image name (without registry prefix)
      stack: string             # Docker stack name
      replicas: int             # Number of replicas (default: 1)
      health_endpoint: string   # Health check path (optional)
```

### `deployment.environments`

Configure deployment targets:

```yaml
deployment:
  environments:
    staging:
      host: string              # SSH hostname for Swarm manager
      ssh_user: string          # SSH username (default: deploy)
      ssh_key_secret: string    # 1Password item with SSH key
      auto_deploy_branch: string # Branch to auto-deploy (optional)

    production:
      host: string
      ssh_user: string
      require_approval: bool    # Block deploys requiring approval
      approval_environment: string  # GitHub environment name
```

### Complete Example

```yaml
deployment:
  registry: ghcr.io
  organization: my-org

  services:
    api:
      image: myapp-api
      stack: myapp
      replicas: 3
      health_endpoint: /health

    worker:
      image: myapp-worker
      stack: myapp
      replicas: 2

  environments:
    staging:
      host: staging.example.com
      ssh_user: deploy
      auto_deploy_branch: main

    production:
      host: prod.example.com
      ssh_user: deploy
      require_approval: true
      approval_environment: production
```

---

## `development`

Local development environment configuration.

```yaml
development:
  compose_file: string      # Docker Compose file path
                            # Default: docker-compose.yml

  services:                 # Services to start by default
    - service1
    - service2

  env:                      # Environment variables for compose
    KEY: value

  ports:                    # Port documentation
    service: port
```

### Example

```yaml
development:
  compose_file: docker-compose.yml

  services:
    - db
    - api
    - web

  env:
    DATABASE_URL: postgresql://postgres:postgres@db:5432/myapp
    API_PORT: "3000"
    DEBUG: "true"

  ports:
    api: 3000
    web: 8080
    db: 5432
```

---

## `infrastructure`

Shared Traefik infrastructure settings.

```yaml
infrastructure:
  enabled: bool             # Enable shared infrastructure
                            # Default: false

  network_name: string      # Docker network name
                            # Default: devflow-proxy

  legacy_networks:          # Networks to migrate from
    - proxy
    - old-network
```

### `infrastructure.traefik`

```yaml
infrastructure:
  traefik:
    http_port: int          # HTTP port (default: 80)
    https_port: int         # HTTPS port (default: 443)
    dashboard_port: int     # Dashboard port (default: 8088)
    dashboard_enabled: bool # Enable dashboard (default: true)
    log_level: string       # Log level (default: INFO)
```

### `infrastructure.certificates`

```yaml
infrastructure:
  certificates:
    domains:                # Domains for certificates
      - "*.localhost"
      - "*.myapp.localhost"

    cert_dir: string        # Certificate directory
                            # Default: ~/.devflow/certs
```

### Complete Example

```yaml
infrastructure:
  enabled: true
  network_name: devflow-proxy

  traefik:
    http_port: 80
    https_port: 443
    dashboard_port: 8088
    dashboard_enabled: true
    log_level: INFO

  certificates:
    domains:
      - "*.localhost"
      - "*.myapp.localhost"
      - "*.api.localhost"
    cert_dir: ~/.devflow/certs
```

---

## `git`

Project-level git configuration. Overrides global settings for this project.

```yaml
git:
  user:
    name: string            # Git user name (optional)
    email: string           # Git user email (optional)

  co_author:
    enabled: bool           # Enable Claude co-author (default: true)
    name: string            # Co-author name (default: Claude)
    email: string           # Co-author email (default: noreply@anthropic.com)
```

### Example

```yaml
git:
  user:
    name: "Project Team"
    email: "team@example.com"

  co_author:
    enabled: true
    name: "Claude"
    email: "noreply@anthropic.com"
```

To disable Claude co-author for a project:

```yaml
git:
  co_author:
    enabled: false
```

---

## Environment Variables

Devflow recognizes these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEVFLOW_ENV` | Current environment | `local` |
| `DATABASE_URL` | Database connection URL | - |

---

## Validation

Validate your configuration:

```bash
devflow config validate
```

View current configuration:

```bash
devflow config show
devflow config show --format json
```

---

## Full Example

```yaml
version: "1"

project:
  name: myapp

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
    production:
      url_secret: app_database_url
      host: prod.example.com
      ssh_user: deploy
      require_approval: true

secrets:
  provider: 1password
  vault: Development
  github:
    auth: app  # Use GitHub App instead of gh CLI
    app:
      app_id: op://Development/GitHub-App/app_id
      installation_id: op://Development/GitHub-App/installation_id
      private_key: op://Development/GitHub-App/private_key
  mappings:
    - name: database_url
      op_item: "Database"
      op_field: url
      github_secret: DATABASE_URL
      docker_secret: app_database_url

deployment:
  registry: ghcr.io
  organization: my-org
  services:
    api:
      image: myapp-api
      stack: myapp
      replicas: 2
  environments:
    staging:
      host: staging.example.com
      ssh_user: deploy
    production:
      host: prod.example.com
      ssh_user: deploy
      require_approval: true

development:
  compose_file: docker-compose.yml
  services:
    - db
    - api

infrastructure:
  enabled: true
  network_name: devflow-proxy
  certificates:
    domains:
      - "*.localhost"
      - "*.myapp.localhost"

git:
  co_author:
    enabled: true
```
