# Commands Reference

Complete reference for all devflow CLI commands.

## Global Options

```bash
devflow [OPTIONS] COMMAND [ARGS]
```

| Option | Description |
|--------|-------------|
| `--verbose`, `-v` | Enable verbose output |
| `--help` | Show help message |
| `--version` | Show version |

---

## Root Commands

### `devflow init`

Initialize devflow configuration in the current project.

```bash
devflow init [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--preset`, `-p` | Use a built-in preset (`aocodex`, `aosentry`) |
| `--force`, `-f` | Overwrite existing configuration |

**Example:**
```bash
devflow init
devflow init --preset aocodex
devflow init --force
```

---

### `devflow doctor`

Check system health and verify all required tools.

```bash
devflow doctor [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--fix` | Attempt to fix issues automatically |

**Output:**
- Tool installation status (gh, op, docker, supabase, psql, git)
- Authentication status for each tool
- Global setup status (whether `devflow install` has been run)
- Global config location and settings (git name/email)
- Project config location (devflow.yml)

**Example output:**
```
Configuration Status
  Global setup: Completed
  Global config: /home/user/.devflow/config.yml
    Git name: Your Name
    Git email: your@email.com
  Project config: /path/to/project/devflow.yml
```

---

### `devflow version`

Display the current devflow version.

```bash
devflow version
```

---

### `devflow install`

First-time devflow setup wizard. Configures global settings, git, and shared infrastructure.

```bash
devflow install [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--skip-plugin` | Skip Claude Code plugin installation |
| `--skip-git` | Skip git configuration |
| `--skip-infra` | Skip infrastructure setup |
| `--non-interactive`, `-y` | Use defaults without prompts |
| `--force`, `-f` | Re-run setup (overwrites existing config) |

**Setup steps:**
1. Create `~/.devflow/` directory structure
2. Configure git user name and email
3. Set default secrets provider and container registry
4. Create Docker network for shared infrastructure
5. Generate local HTTPS certificates (if mkcert available)
6. Install Claude Code plugin

**Examples:**
```bash
devflow install              # Interactive setup
devflow install -y           # Non-interactive with defaults
devflow install --force      # Re-run setup
devflow install --skip-infra # Skip infrastructure
```

**Subcommands:**
```bash
devflow install uninstall  # Remove Claude Code plugin
devflow install status     # Show installation status
```

---

## `devflow dev` - Local Development

Commands for managing local development environment.

### `devflow dev setup`

Set up local development environment.

```bash
devflow dev setup [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |

**Operations:**
1. Check Docker daemon
2. Load project configuration
3. Configure local git user (from project's `git` config)
4. Pull Docker images
5. Set up `.env` from template
6. Resolve 1Password references
7. Start infrastructure (if configured)

---

### `devflow dev start`

Start local development services.

```bash
devflow dev start [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--service`, `-s` | Start specific service only |
| `--detach`, `-d` | Run in background (default) |
| `--no-detach` | Run in foreground |

**Examples:**
```bash
devflow dev start
devflow dev start --service api
devflow dev start --no-detach
```

---

### `devflow dev stop`

Stop local development services.

```bash
devflow dev stop [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--service`, `-s` | Stop specific service only |

---

### `devflow dev logs`

View service logs.

```bash
devflow dev logs SERVICE [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--follow`, `-f` | Follow log output |
| `--tail`, `-n` | Number of lines (default: 100) |

**Example:**
```bash
devflow dev logs api --follow
devflow dev logs db --tail 50
```

---

### `devflow dev shell`

Open a shell in a running container.

```bash
devflow dev shell SERVICE [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--shell` | Shell to use (default: `/bin/sh`) |

**Example:**
```bash
devflow dev shell api
devflow dev shell api --shell /bin/bash
```

---

### `devflow dev reset`

Reset local development environment.

```bash
devflow dev reset [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--volumes`, `-v` | Also remove volumes (deletes data) |

**Warning:** Prompts for confirmation before destructive operations.

---

## `devflow db` - Database

Commands for database and migration management.

### `devflow db status`

Show migration status.

```bash
devflow db status [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--env`, `-e` | Environment (default: `local`) |
| `--json` | Output as JSON |

**Output:**
- Executor type
- Applied/pending/total migrations
- List of pending files

---

### `devflow db migrate`

Apply pending migrations.

```bash
devflow db migrate [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--env`, `-e` | Environment (default: `local`) |
| `--dry-run` | Show what would be applied |
| `--ci` | CI mode (non-interactive) |
| `--json` | Output as JSON |

**Examples:**
```bash
devflow db migrate
devflow db migrate --env staging
devflow db migrate --dry-run
devflow db migrate --env production --ci
```

---

### `devflow db create`

Create a new migration file.

```bash
devflow db create NAME
```

**Example:**
```bash
devflow db create add_user_preferences
# Creates: migrations/20240115120000_add_user_preferences.sql
```

---

### `devflow db rollback`

Rollback migrations.

```bash
devflow db rollback [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--env`, `-e` | Environment (default: `local`) |
| `--steps`, `-n` | Number of migrations (default: 1) |
| `--dry-run` | Show what would be rolled back |
| `--force` | Required for production rollback |
| `--json` | Output as JSON |

**Requirements:** Each migration needs a corresponding `.down.sql` file.

**Examples:**
```bash
devflow db rollback
devflow db rollback --steps 2
devflow db rollback --env production --force
```

---

### `devflow db connect`

Open a psql session.

```bash
devflow db connect [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--env`, `-e` | Environment (default: `local`) |

---

## `devflow deploy` - Deployment

Commands for deploying to Docker Swarm clusters.

### `devflow deploy status`

Show deployment status.

```bash
devflow deploy status [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--env`, `-e` | Environment (default: `staging`) |
| `--service`, `-s` | Specific service only |
| `--json` | Output as JSON |

---

### `devflow deploy staging`

Deploy to staging (no confirmation required).

```bash
devflow deploy staging [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--service`, `-s` | Deploy specific service |
| `--migrate`, `-m` | Run migrations first |
| `--dry-run` | Show what would be deployed |
| `--json` | Output as JSON |

**Example:**
```bash
devflow deploy staging
devflow deploy staging --service api --migrate
```

---

### `devflow deploy production`

Deploy to production (requires confirmation).

```bash
devflow deploy production [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--service`, `-s` | Deploy specific service |
| `--migrate`, `-m` | Run migrations first |
| `--dry-run` | Show what would be deployed |
| `--yes`, `-y` | Skip confirmation |
| `--json` | Output as JSON |

**Note:** If `require_approval` is set in config, deploys are blocked.

---

### `devflow deploy rollback`

Rollback to previous deployment.

```bash
devflow deploy rollback [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--env`, `-e` | Environment (default: `staging`) |
| `--service`, `-s` | Specific service |
| `--json` | Output as JSON |

---

### `devflow deploy logs`

View service logs.

```bash
devflow deploy logs SERVICE [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--env`, `-e` | Environment (default: `staging`) |
| `--follow`, `-f` | Follow log output |
| `--tail`, `-n` | Lines to show (default: 100) |
| `--json` | Output as JSON |

---

### `devflow deploy ssh`

SSH to a cluster node.

```bash
devflow deploy ssh [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--env`, `-e` | Environment (default: `staging`) |
| `--node` | Node to connect to (default: `manager`) |
| `--json` | Output as JSON |

---

## `devflow secrets` - Secrets Management

Commands for managing secrets across systems.

### `devflow secrets list`

List secrets from a source.

```bash
devflow secrets list [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--env`, `-e` | Environment (default: `staging`) |
| `--source`, `-s` | Source (`1password`, `github`, `docker`) |
| `--auth`, `-a` | GitHub auth method: `cli`, `app`, or `auto` (default: `auto`) |
| `--json` | Output as JSON |

---

### `devflow secrets sync`

Sync secrets between systems.

```bash
devflow secrets sync [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--from` | Source (default: `1password`) |
| `--to` | Target (default: `github`) |
| `--env`, `-e` | Environment (default: `staging`) |
| `--auth`, `-a` | GitHub auth method: `cli`, `app`, or `auto` (default: `auto`) |
| `--dry-run` | Show what would be synced |
| `--json` | Output as JSON |

**Auth Methods:**
- `cli` - Use the `gh` CLI (requires `gh auth login`)
- `app` - Use GitHub App authentication (requires config)
- `auto` - Use App if configured, otherwise fall back to CLI

**Examples:**
```bash
devflow secrets sync --from 1password --to github
devflow secrets sync --to docker --dry-run
devflow secrets sync --to github --auth app  # Force GitHub App
devflow secrets sync --to github --auth cli  # Force gh CLI
```

---

### `devflow secrets verify`

Verify secrets are in sync.

```bash
devflow secrets verify [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--env`, `-e` | Environment (default: `staging`) |
| `--auth`, `-a` | GitHub auth method: `cli`, `app`, or `auto` (default: `auto`) |
| `--json` | Output as JSON |

**Output:** Shows each secret's presence in 1Password, GitHub, and Docker.

---

### `devflow secrets export`

Export secrets to `.env` format.

```bash
devflow secrets export [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--env`, `-e` | Environment (default: `local`) |
| `--output`, `-o` | Output file (`-` for stdout) |
| `--json` | Output as JSON |

**Restriction:** Only works for local/development environments.

---

## `devflow config` - Configuration

Commands for managing devflow configuration.

### `devflow config show`

Display current configuration.

```bash
devflow config show [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--format`, `-f` | Format (`yaml` or `json`) |

---

### `devflow config validate`

Validate configuration file.

```bash
devflow config validate
```

---

### `devflow config env`

Show or switch environment.

```bash
devflow config env [ENVIRONMENT]
```

**Examples:**
```bash
devflow config env         # Show current
devflow config env staging # Switch to staging
```

---

### `devflow config set`

Set a configuration value.

```bash
devflow config set KEY VALUE [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |

**Examples:**
```bash
devflow config set project.name myapp
devflow config set database.migrations.directory migrations
devflow config set infrastructure.enabled true
devflow config set secrets.mappings '[{"name": "test"}]'
```

---

## `devflow infra` - Infrastructure

Commands for shared development infrastructure.

### `devflow infra up`

Start shared infrastructure.

```bash
devflow infra up [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--detach`, `-d` | Run in background (default) |
| `--force-recreate` | Force recreate containers |
| `--json` | Output as JSON |

---

### `devflow infra down`

Stop shared infrastructure.

```bash
devflow infra down [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--volumes`, `-v` | Remove volumes |
| `--network` | Remove network |
| `--json` | Output as JSON |

---

### `devflow infra status`

Show infrastructure status.

```bash
devflow infra status [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |

---

### `devflow infra configure`

Configure a project to use shared infrastructure.

```bash
devflow infra configure PROJECT_PATH [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--compose`, `-c` | Compose file (default: `docker-compose.yml`) |
| `--dry-run` | Show changes without applying |
| `--no-backup` | Don't create backup |
| `--json` | Output as JSON |

---

### `devflow infra unconfigure`

Restore project's original configuration.

```bash
devflow infra unconfigure PROJECT_PATH [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--compose`, `-c` | Compose file to restore |
| `--json` | Output as JSON |

---

### `devflow infra certs`

Manage TLS certificates.

```bash
devflow infra certs [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--regenerate`, `-r` | Force regenerate |
| `--json` | Output as JSON |

---

### `devflow infra hosts`

Manage /etc/hosts entries.

```bash
devflow infra hosts ACTION [OPTIONS]
```

| Action | Description |
|--------|-------------|
| `list` | Show devflow-managed entries |
| `add` | Add entries for project domains |
| `remove` | Remove devflow-managed entries |

---

### `devflow infra network`

Manage Docker network.

```bash
devflow infra network [ACTION] [OPTIONS]
```

| Action | Description |
|--------|-------------|
| `status` | Show network status (default) |
| `create` | Create network |
| `remove` | Remove network |

---

### `devflow infra doctor`

Check infrastructure health.

```bash
devflow infra doctor [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |
