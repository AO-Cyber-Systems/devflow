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

## Verify Installation

```bash
# Check version
devflow version

# Run health check
devflow doctor
```

The `doctor` command checks all required and optional tools:

```
$ devflow doctor

Tool Installation
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool            ┃ Status  ┃ Version             ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ GitHub CLI      │ ✓       │ gh version 2.40.1   │
│ 1Password CLI   │ ✓       │ 2.24.0              │
│ Docker          │ ✓       │ 24.0.7              │
│ Supabase CLI    │ ✓       │ 1.123.4             │
│ PostgreSQL      │ ✓       │ psql 15.4           │
│ Git             │ ✓       │ git version 2.43.0  │
└─────────────────┴─────────┴─────────────────────┘

Tool Authentication
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Tool            ┃ Status          ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ GitHub CLI      │ ✓ Authenticated │
│ 1Password CLI   │ ✓ Authenticated │
│ Docker          │ ✓ Running       │
└─────────────────┴─────────────────┘
```

## Initialize a Project

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

## Post-Installation Setup

### 1. Configure Docker

Ensure Docker daemon is running:

```bash
docker info
```

### 2. Authenticate 1Password CLI (Optional)

```bash
eval $(op signin)
```

### 3. Authenticate GitHub CLI (Optional)

```bash
gh auth login
```

### 4. Install Local CA (Optional)

For local HTTPS support:

```bash
# Install mkcert
brew install mkcert

# Install local CA to system trust store
mkcert -install

# Verify CA installation
devflow infra doctor
```

## Claude Code Integration

Devflow includes a Claude Code plugin for AI-assisted development:

```bash
# Install the Claude Code plugin
devflow install

# Check installation status
devflow install status

# Uninstall if needed
devflow install uninstall
```

## Next Steps

- [Configure your project](Configuration.md)
- [Set up local development](Use-Cases.md#local-development-setup)
- [Learn the commands](Commands.md)
