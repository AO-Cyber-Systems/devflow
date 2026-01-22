# Installation

## Prerequisites

### Required

- **Python 3.10 or higher**
- **Docker** with Docker Compose v2
- **Git**

### Optional Tools

Depending on which features you use, you may need additional tools:

| Tool | Required For | Installation |
|------|--------------|--------------|
| [1Password CLI](https://1password.com/downloads/command-line/) | Secrets management | `brew install 1password-cli` |
| [GitHub CLI](https://cli.github.com/) | GitHub secrets sync | `brew install gh` |
| [mkcert](https://github.com/FiloSottile/mkcert) | Local HTTPS | `brew install mkcert` |
| [Supabase CLI](https://supabase.com/docs/guides/cli) | Supabase migrations | `brew install supabase/tap/supabase` |
| [PostgreSQL client](https://www.postgresql.org/) | `db connect` command | `brew install postgresql` |

## Install Devflow

### From PyPI (Recommended)

```bash
pip install devflow
```

### From Source

```bash
git clone https://github.com/AO-Cyber-Systems/devflow.git
cd devflow
pip install -e .
```

### With pipx (Isolated Environment)

```bash
pipx install devflow
```

## First-Time Setup

After installing devflow, run the setup wizard to configure your environment:

```bash
devflow install
```

This interactive wizard guides you through:

1. **Create directories** - Creates `~/.devflow/` for global configuration
2. **Git configuration** - Detects existing git config or prompts for name/email
3. **Default preferences** - Sets your preferred secrets provider and container registry
4. **Infrastructure setup** - Creates Docker network and optionally generates local HTTPS certificates
5. **Claude Code plugin** - Installs the Claude Code integration for AI-assisted development

### Setup Options

```bash
# Run with all defaults (non-interactive)
devflow install -y

# Skip specific steps
devflow install --skip-git        # Skip git configuration
devflow install --skip-plugin     # Skip Claude Code plugin
devflow install --skip-infra      # Skip infrastructure setup

# Re-run setup (overwrites existing config)
devflow install --force
```

### What Gets Created

After setup, your `~/.devflow/` directory contains:

```
~/.devflow/
├── config.yml          # Global configuration
├── certs/              # Local HTTPS certificates (optional)
│   ├── cert.pem
│   └── key.pem
└── plugins/            # Installed plugins
    └── devflow.mdc     # Claude Code plugin
```

### Global Configuration

The `~/.devflow/config.yml` stores user-wide settings:

```yaml
version: "1"
git:
  user_name: "Your Name"
  user_email: "your@email.com"
  co_author_enabled: true
  co_author_name: "Claude"
  co_author_email: "noreply@anthropic.com"
defaults:
  secrets_provider: 1password  # or: env, null
  network_name: devflow-proxy
  registry: ghcr.io
infrastructure:
  auto_start: false
  traefik_http_port: 80
  traefik_https_port: 443
  traefik_dashboard_port: 8088
setup_completed: true
```

## Verify Installation

```bash
# Check version
devflow version

# Run health check
devflow doctor
```

The `doctor` command checks all required tools, authentication status, and configuration:

```
$ devflow doctor

Devflow System Health Check

Tool Installation
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool              ┃ Binary   ┃ Status    ┃ Version             ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ GitHub CLI        │ gh       │ Installed │ gh version 2.40.1   │
│ 1Password CLI     │ op       │ Installed │ 2.24.0              │
│ Docker            │ docker   │ Installed │ 24.0.7              │
│ Supabase CLI      │ supabase │ Installed │ 1.123.4             │
│ PostgreSQL Client │ psql     │ Installed │ psql 15.4           │
│ Git               │ git      │ Installed │ git version 2.43.0  │
└───────────────────┴──────────┴───────────┴─────────────────────┘

Authentication Status
┏━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Tool     ┃ Status  ┃ Details       ┃
┡━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ gh       │ OK      │ Authenticated │
│ op       │ OK      │ Signed in     │
│ docker   │ OK      │ Running       │
│ supabase │ OK      │ Ready         │
└──────────┴─────────┴───────────────┘

Configuration Status
  Global setup: Completed
  Global config: /home/user/.devflow/config.yml
    Git name: Your Name
    Git email: your@email.com
  Project config: Not found (run 'devflow init' to create)

Summary
  All required tools are installed.
```

## Initialize a Project

After global setup, initialize devflow in your project:

```bash
cd your-project
devflow init
```

This creates a `devflow.yml` configuration file. You can also use a preset:

```bash
# Use a built-in preset
devflow init --preset aocodex

# Force overwrite existing config
devflow init --force
```

## Tool Authentication

Some tools require authentication to use their features:

### 1Password CLI

```bash
# Sign in (creates session)
eval $(op signin)

# Or use biometric unlock if configured
op signin --biometric
```

### GitHub CLI

```bash
gh auth login
```

### Docker

Ensure Docker daemon is running:

```bash
docker info
```

## Local HTTPS Setup

For local HTTPS support with valid certificates:

```bash
# Install mkcert (if not already installed)
brew install mkcert

# Install local CA to system trust store
mkcert -install
```

If you ran `devflow install` with infrastructure enabled, certificates are already generated in `~/.devflow/certs/`. Otherwise, you can generate them manually:

```bash
# Start shared infrastructure (generates certs if needed)
devflow infra up

# Verify setup
devflow infra doctor
```

## Troubleshooting

### "Devflow not set up" warning

Run the setup wizard:

```bash
devflow install
```

### Missing tools

Install the required tool and run doctor again:

```bash
# Example: Install PostgreSQL client
brew install postgresql

# Verify
devflow doctor
```

### Permission denied for Docker

Add your user to the docker group:

```bash
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

### Certificate issues

Reinstall the local CA:

```bash
mkcert -install
devflow infra up
```

## Next Steps

- [Configure your project](Configuration.md)
- [Set up local development](Use-Cases.md#local-development-setup)
- [Learn the commands](Commands.md)
