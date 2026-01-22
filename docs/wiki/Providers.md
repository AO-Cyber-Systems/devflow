# Providers

Devflow integrates with external tools through a provider system. Each provider wraps a CLI tool and exposes its functionality.

## Overview

| Provider | Binary | Purpose |
|----------|--------|---------|
| [Docker](#docker-provider) | `docker` | Container and Swarm management |
| [1Password](#1password-provider) | `op` | Secrets management |
| [GitHub](#github-provider) | `gh` | Repository and Actions integration |
| [SSH](#ssh-provider) | `ssh` | Remote server operations |
| [Supabase](#supabase-provider) | `supabase` | Database migrations |
| [Mkcert](#mkcert-provider) | `mkcert` | Local TLS certificates |
| [Infrastructure](#infrastructure-provider) | - | Shared Traefik management |

---

## Docker Provider

Manages Docker containers, Swarm services, and secrets.

### Requirements

- Docker Engine installed and running
- Docker Compose v2

### Capabilities

| Method | Description |
|--------|-------------|
| `is_authenticated()` | Check if Docker daemon is running |
| `list_secrets()` | List Docker Swarm secrets |
| `create_secret(name, value)` | Create a new secret |
| `remove_secret(name)` | Remove a secret |
| `secret_exists(name)` | Check if secret exists |
| `list_services(filter)` | List Swarm services |
| `service_update(service, image)` | Update service image |
| `service_logs(service, tail, follow)` | Stream service logs |
| `service_rollback(service)` | Rollback to previous version |

### Installation

```bash
# macOS
brew install docker

# Linux (Ubuntu/Debian)
sudo apt-get install docker.io docker-compose-plugin

# Verify
docker --version
docker compose version
```

### Authentication

The Docker provider checks if the Docker daemon is running:

```bash
docker info
```

### Usage in devflow

```bash
# Local development
devflow dev start
devflow dev stop
devflow dev logs api

# Swarm operations
devflow deploy status
devflow secrets list --source docker
```

---

## 1Password Provider

Integrates with 1Password for secrets management.

### Requirements

- 1Password CLI (`op`) version 2.0+
- 1Password account with CLI access enabled

### Capabilities

| Method | Description |
|--------|-------------|
| `is_authenticated()` | Check if signed into 1Password |
| `list_vaults()` | List available vaults |
| `list_items(vault)` | List items in a vault |
| `get_item(item, vault)` | Get complete item details |
| `read_field(item, field, vault)` | Read specific field value |
| `inject(template)` | Resolve `op://` references in text |

### Installation

```bash
# macOS
brew install 1password-cli

# Linux
curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
  sudo gpg --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" | \
  sudo tee /etc/apt/sources.list.d/1password.list
sudo apt update && sudo apt install 1password-cli

# Verify
op --version
```

### Authentication

```bash
# Interactive sign-in
eval $(op signin)

# Check status
op whoami
```

### 1Password References

Use `op://` URIs to reference secrets:

```
op://VaultName/ItemName/FieldName
```

Example `.env.template`:
```bash
DATABASE_URL=op://Development/Database/connection_string
API_KEY=op://Development/APIs/stripe_key
```

### Usage in devflow

```bash
# List secrets
devflow secrets list --source 1password

# Sync to GitHub
devflow secrets sync --from 1password --to github

# Export for local dev
devflow secrets export --output .env.local

# Automatic resolution in dev setup
devflow dev setup  # Resolves op:// in .env.template
```

---

## GitHub Provider

Integrates with GitHub for repository operations and Actions secrets.

### Requirements

- GitHub CLI (`gh`) version 2.0+
- Authenticated with GitHub

### Capabilities

| Method | Description |
|--------|-------------|
| `is_authenticated()` | Check GitHub CLI auth status |
| `get_current_user()` | Get authenticated username |
| `list_secrets(repo)` | List repository secrets |
| `set_secret(repo, name, value)` | Create/update secret |
| `delete_secret(repo, name)` | Delete a secret |
| `get_workflow_runs(repo, limit)` | Get recent workflow runs |

### Installation

```bash
# macOS
brew install gh

# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh

# Verify
gh --version
```

### Authentication

```bash
# Interactive login
gh auth login

# Check status
gh auth status
```

### Usage in devflow

```bash
# List GitHub secrets
devflow secrets list --source github

# Sync secrets to GitHub
devflow secrets sync --from 1password --to github

# Verify sync status
devflow secrets verify
```

---

## SSH Provider

Handles remote server connections for deployments and database operations.

### Requirements

- OpenSSH client (`ssh`)
- SCP for file transfers (optional)

### Capabilities

| Method | Description |
|--------|-------------|
| `execute(host, user, command)` | Run command on remote server |
| `connect(host, user)` | Interactive SSH session |
| `create_tunnel(local, remote_host, remote_port)` | Create SSH tunnel |
| `write_temp_key(content)` | Write SSH key to temp file |
| `cleanup_temp_key(path)` | Securely remove temp key |
| `copy_to_remote(local, remote, host, user)` | SCP file transfer |

### SSH Key from 1Password

Configure SSH key retrieval from 1Password:

```yaml
deployment:
  environments:
    staging:
      host: staging.example.com
      ssh_user: deploy
      ssh_key_secret: "SSH Keys/deploy_key"  # 1Password item
```

### Usage in devflow

```bash
# SSH to server
devflow deploy ssh --env staging

# Commands use SSH automatically
devflow deploy status --env staging
devflow deploy staging
devflow db migrate --env staging
```

### Security Notes

- Uses `-o StrictHostKeyChecking=accept-new` for automation
- Temporary SSH keys are written with 0600 permissions
- Keys are cleaned up after use

---

## Supabase Provider

Integrates with Supabase CLI for database migrations.

### Requirements

- Supabase CLI (`supabase`)
- Works with self-hosted Supabase (no Cloud project required)

### Capabilities

| Method | Description |
|--------|-------------|
| `is_authenticated()` | Always true (uses --db-url) |
| `db_push(url, migrations_dir, dry_run)` | Apply migrations |
| `db_pull(url, schema)` | Pull remote schema |
| `db_diff(url, schema)` | Generate diff SQL |

### Installation

```bash
# macOS
brew install supabase/tap/supabase

# npm
npm install -g supabase

# Verify
supabase --version
```

### Self-Hosted Usage

The provider uses `--db-url` flag, bypassing `supabase link`:

```bash
supabase db push --db-url postgresql://... --include-all
```

### Configuration

```yaml
database:
  migrations:
    format: supabase  # or use_supabase_cli: true
    directory: supabase/migrations
```

### Usage in devflow

```bash
# Apply migrations
devflow db migrate --env staging

# Check status
devflow db status
```

---

## Mkcert Provider

Generates locally-trusted TLS certificates.

### Requirements

- mkcert installed
- CA installed in system trust store

### Capabilities

| Method | Description |
|--------|-------------|
| `is_ca_installed()` | Check if CA is trusted |
| `install_ca()` | Install CA to trust store |
| `cert_exists(output_dir)` | Check for existing certs |
| `generate_cert(domains, output_dir)` | Generate certificates |
| `get_ca_root()` | Get CA root directory |

### Installation

```bash
# macOS
brew install mkcert

# Linux
sudo apt install libnss3-tools
brew install mkcert  # or build from source

# Install CA (one-time)
mkcert -install
```

### Usage in devflow

```bash
# Check certificate status
devflow infra certs

# Regenerate certificates
devflow infra certs --regenerate

# Check infrastructure health
devflow infra doctor
```

### Generated Certificates

Certificates are stored in `~/.devflow/certs/`:
- `localhost.pem` - Certificate
- `localhost-key.pem` - Private key

Default domains:
- `*.localhost`
- `*.aocodex.localhost`
- `*.aosentry.localhost`

---

## Infrastructure Provider

Manages shared Traefik infrastructure for multiple projects.

### Requirements

- Docker
- Mkcert (for HTTPS)

### Capabilities

| Method | Description |
|--------|-------------|
| `start()` | Start Traefik and network |
| `stop()` | Stop infrastructure |
| `status()` | Get current status |
| `regenerate_certificates()` | Update TLS certs |
| `register_project(project)` | Register project |
| `unregister_project(path)` | Remove project |
| `get_registered_projects()` | List projects |
| `doctor()` | Health checks |

### Data Storage

| Location | Purpose |
|----------|---------|
| `~/.devflow/` | Infrastructure home |
| `~/.devflow/projects.json` | Project registry |
| `~/.devflow/certs/` | TLS certificates |
| `~/.devflow/infrastructure/` | Traefik config |

### Usage in devflow

```bash
# Start infrastructure
devflow infra up

# Check status
devflow infra status

# Configure project
devflow infra configure /path/to/project

# Health check
devflow infra doctor
```

### Traefik Configuration

Default settings:
- HTTP: Port 80
- HTTPS: Port 443
- Dashboard: Port 8088

Access the dashboard at: http://localhost:8088

---

## Provider Health Check

Use `devflow doctor` to check all providers:

```bash
devflow doctor
```

Output shows:
- Installation status for each tool
- Authentication status
- Version information
- Configuration file locations

For infrastructure-specific checks:

```bash
devflow infra doctor
```
