# PRD-007: Secrets & Environment Management

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)

---

## Overview

DevFlow requires secure management of secrets and environment variables across multiple deployment modes (Local, SaaS, On-Premise). This PRD defines a flexible, secure secrets management strategy that supports 1Password integration (recommended) with .env file fallback (required), ensuring both enterprise-grade security and developer simplicity.

---

## Goals

### Primary Goals
1. **Secure by Default**: Encourage best practices while remaining accessible
2. **Deployment Flexibility**: Support local dev, SaaS, and on-premise deployments
3. **1Password Integration**: First-class support for enterprise secret vaults
4. **Developer Friendly**: Simple .env fallback for quick starts and demos
5. **Project Isolation**: Per-project environment variable management

### Secondary Goals
1. Automatic secret rotation workflows
2. Audit logging of secret access
3. Team-level secret sharing
4. Compliance support (SOC2, HIPAA)
5. Migration paths between secret stores

---

## Secrets Architecture

### Three-Tier Secret Model

```
┌─────────────────────────────────────────────────────────────┐
│               TIER 1: SYSTEM SECRETS                        │
│               (Infrastructure & Core Services)              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  - Database connection strings                              │
│  - Root encryption keys                                     │
│  - Service-to-service authentication                        │
│  - AOSentry API keys (LLM gateway)                         │
│                                                             │
│  Storage: 1Password (production) or .env (development)      │
│  Access: System administrators only                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│               TIER 2: USER SECRETS                          │
│               (Personal Integration Tokens)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  - OAuth tokens (Jira, GitHub, Confluence)                  │
│  - Personal API keys                                        │
│  - User-specific LLM keys (if not using AOSentry)          │
│                                                             │
│  Storage: Encrypted in PostgreSQL + 1Password backup        │
│  Access: Individual users only                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│               TIER 3: PROJECT SECRETS                       │
│               (Project-Specific Configuration)              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  - API endpoints (staging vs production)                    │
│  - Feature flags                                            │
│  - Project-specific API keys                                │
│  - Environment-specific variables                           │
│                                                             │
│  Storage: 1Password vaults (per project) or .env files      │
│  Access: Project team members                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Secret Resolution Priority

DevFlow uses a **cascade priority system** for resolving secrets:

```
Priority 1: 1Password (if OP_CONNECT_TOKEN configured)
    ↓ (fallback if 1Password unavailable)
Priority 2: .env file (if exists in project root)
    ↓ (fallback if not in .env file)
Priority 3: Environment variables (system ENV)
    ↓ (if not found in any source)
Error: SecretNotFoundError
```

### Implementation

```python
# services/common/secrets_manager.py

import os
from typing import Optional
from onepasswordconnectsdk.client import Client, new_client
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Unified secrets management with 1Password (recommended) 
    and .env fallback (required).
    """
    
    def __init__(self):
        self.op_client: Optional[Client] = None
        self.env_loaded = False
        
        # Initialize 1Password Connect if configured
        if self._is_onepassword_configured():
            try:
                self.op_client = new_client(
                    url=os.getenv("OP_CONNECT_URL", "http://localhost:8080"),
                    token=os.getenv("OP_CONNECT_TOKEN")
                )
                logger.info("1Password Connect initialized successfully")
            except Exception as e:
                logger.warning(f"1Password initialization failed: {e}. Falling back to .env")
                self.op_client = None
        
        # Load .env file
        if os.path.exists(".env"):
            load_dotenv()
            self.env_loaded = True
            logger.info(".env file loaded")
    
    def _is_onepassword_configured(self) -> bool:
        """Check if 1Password Connect is configured."""
        return bool(os.getenv("OP_CONNECT_TOKEN"))
    
    def get_secret(self, key: str, op_reference: Optional[str] = None) -> str:
        """
        Get secret value with priority cascade.
        
        Args:
            key: Environment variable key (e.g., "OPENAI_API_KEY")
            op_reference: Optional 1Password reference (e.g., "op://DevFlow/OpenAI/api_key")
        
        Returns:
            Secret value
        
        Raises:
            SecretNotFoundError: If secret not found in any source
        
        Example:
            >>> secrets = SecretsManager()
            >>> api_key = secrets.get_secret(
            ...     key="AOSENTRY_API_KEY",
            ...     op_reference="op://DevFlow/AOSentry/api_key"
            ... )
        """
        
        # Priority 1: 1Password
        if self.op_client and op_reference:
            try:
                value = self._get_from_onepassword(op_reference)
                if value:
                    logger.debug(f"Secret '{key}' retrieved from 1Password")
                    return value
            except Exception as e:
                logger.warning(f"1Password lookup failed for '{key}': {e}")
        
        # Priority 2: .env file
        if self.env_loaded:
            value = os.getenv(key)
            if value:
                logger.debug(f"Secret '{key}' retrieved from .env file")
                return value
        
        # Priority 3: System environment variables
        value = os.getenv(key)
        if value:
            logger.debug(f"Secret '{key}' retrieved from system ENV")
            return value
        
        # Not found in any source
        raise SecretNotFoundError(
            f"Secret '{key}' not found in 1Password, .env file, or environment variables"
        )
    
    def _get_from_onepassword(self, reference: str) -> Optional[str]:
        """
        Retrieve secret from 1Password using reference.
        
        Format: op://vault/item/field
        Example: op://DevFlow/AOSentry/api_key
        """
        if not self.op_client:
            return None
        
        # Parse reference: op://vault/item/field
        if not reference.startswith("op://"):
            raise ValueError(f"Invalid 1Password reference: {reference}")
        
        parts = reference.replace("op://", "").split("/")
        if len(parts) != 3:
            raise ValueError(f"Invalid 1Password reference format: {reference}")
        
        vault_name, item_name, field_name = parts
        
        # Fetch item from 1Password
        try:
            item = self.op_client.get_item(item_name, vault_name)
            
            # Find field in item
            for field in item.fields:
                if field.label == field_name or field.id == field_name:
                    return field.value
            
            logger.warning(f"Field '{field_name}' not found in 1Password item '{item_name}'")
            return None
            
        except Exception as e:
            logger.error(f"1Password API error: {e}")
            return None


class SecretNotFoundError(Exception):
    """Raised when secret cannot be found in any configured source."""
    pass


# Global instance
secrets_manager = SecretsManager()


# Convenience function
def get_secret(key: str, op_reference: Optional[str] = None) -> str:
    """Get secret from configured secret store."""
    return secrets_manager.get_secret(key, op_reference)
```

---

## 1Password Integration

### Setup for Production/Enterprise

#### 1. Deploy 1Password Connect Server

```yaml
# docker-compose.1password.yml

version: '3.8'

services:
  onepassword-connect:
    image: 1password/connect-api:latest
    container_name: devflow-1password-connect
    ports:
      - "8080:8080"
    volumes:
      - ./secrets/1password-credentials.json:/home/opuser/.op/1password-credentials.json:ro
      - onepassword-data:/home/opuser/.op/data
    environment:
      OP_SESSION: ${OP_SESSION}
    restart: unless-stopped
    networks:
      - devflow-internal
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  onepassword-data:
    driver: local

networks:
  devflow-internal:
    driver: bridge
```

#### 2. Configure DevFlow to Use 1Password

```bash
# .env.production

# 1Password Connect Configuration
OP_CONNECT_URL=http://onepassword-connect:8080
OP_CONNECT_TOKEN=<your-service-account-token>

# Secrets will be resolved from 1Password automatically
# No need to set actual values here - just references
```

#### 3. Create Vault Structure in 1Password

```
1Password Vault: "DevFlow"
├── Item: "AOSentry"
│   ├── api_key: "sk-proj-xxx..."
│   └── endpoint: "https://aosentry.aocodex.ai"
│
├── Item: "PostgreSQL"
│   ├── connection_url: "postgresql://user:pass@host:5432/db"
│   ├── username: "devflow"
│   └── password: "<secure-password>"
│
├── Item: "Qdrant"
│   ├── url: "http://qdrant:6333"
│   └── api_key: "<your-qdrant-key>"
│
├── Item: "Atlassian"
│   ├── oauth_client_id: "xxx"
│   └── oauth_client_secret: "yyy"
│
└── Item: "GitHub"
    ├── oauth_client_id: "xxx"
    └── oauth_client_secret: "yyy"
```

#### 4. Reference Secrets in Configuration

```yaml
# config/secrets.yaml (production)

database:
  url: "op://DevFlow/PostgreSQL/connection_url"

vector_store:
  qdrant:
    url: "op://DevFlow/Qdrant/url"
    api_key: "op://DevFlow/Qdrant/api_key"

llm:
  aosentry:
    api_key: "op://DevFlow/AOSentry/api_key"
    endpoint: "op://DevFlow/AOSentry/endpoint"

integrations:
  atlassian:
    oauth_client_id: "op://DevFlow/Atlassian/oauth_client_id"
    oauth_client_secret: "op://DevFlow/Atlassian/oauth_client_secret"
  
  github:
    oauth_client_id: "op://DevFlow/GitHub/oauth_client_id"
    oauth_client_secret: "op://DevFlow/GitHub/oauth_client_secret"
```

---

## Environment File Management

### .env File Structure

```bash
# .env.example
# Copy this file to .env and fill in your values
# NEVER commit .env to git - it contains secrets!

# ============================================
# DEPLOYMENT MODE
# ============================================
DEVFLOW_MODE=local  # local, hybrid, saas, onprem

# ============================================
# 1PASSWORD (OPTIONAL - RECOMMENDED FOR PRODUCTION)
# ============================================
# If configured, 1Password takes priority over .env values
# Obtain token from 1Password service account
# OP_CONNECT_URL=http://localhost:8080
# OP_CONNECT_TOKEN=

# ============================================
# DATABASE (Required for local/onprem modes)
# ============================================
# Docker PostgreSQL (default for local development)
DATABASE_URL=postgresql://devflow:devflow@localhost:5432/devflow
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# ============================================
# VECTOR STORE (Required for local/onprem modes)
# ============================================
# Docker Qdrant (default for local development)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=devflow_knowledge

# ============================================
# AOSENTRY - LLM GATEWAY (Required for all modes)
# ============================================
# All LLM calls routed through AOSentry (OpenAI API compatible)
AOSENTRY_API_URL=https://aosentry.aocodex.ai
AOSENTRY_API_KEY=your-aosentry-api-key-here

# LLM Preferences (handled by AOSentry)
DEFAULT_CHAT_MODEL=gpt-4-turbo
DEFAULT_EMBEDDING_MODEL=text-embedding-3-large
LLM_TEMPERATURE=0.7

# ============================================
# HOSTED SERVICES (For hybrid/saas modes)
# ============================================
# DEVFLOW_API_URL=https://api.devflow.aocodex.ai
# DEVFLOW_API_KEY=

# ============================================
# INTEGRATION OAUTH CREDENTIALS
# ============================================
# Atlassian (Jira, Confluence)
ATLASSIAN_CLIENT_ID=
ATLASSIAN_CLIENT_SECRET=
ATLASSIAN_REDIRECT_URI=http://localhost:3737/oauth/atlassian/callback

# GitHub
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=http://localhost:3737/oauth/github/callback

# ============================================
# WEBHOOK SECRETS (For integrations)
# ============================================
# Generate with: openssl rand -hex 32
JIRA_WEBHOOK_SECRET=
GITHUB_WEBHOOK_SECRET=
CONFLUENCE_WEBHOOK_SECRET=

# ============================================
# ENCRYPTION & SECURITY
# ============================================
# Secret encryption key (for storing OAuth tokens in DB)
# Generate with: openssl rand -base64 32
SECRET_ENCRYPTION_KEY=

# Session security
SESSION_SECRET=
JWT_SECRET=

# ============================================
# SERVICE PORTS (Local development)
# ============================================
MCP_GATEWAY_PORT=8051
WORKFLOW_ENGINE_PORT=8181
KNOWLEDGE_HUB_PORT=8282
LOCAL_UI_PORT=3737

# ============================================
# LOGGING & MONITORING
# ============================================
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json  # json or text
ENABLE_METRICS=true
METRICS_PORT=9090

# ============================================
# DEVELOPMENT OPTIONS
# ============================================
DEBUG_MODE=false
HOT_RELOAD=true
SKIP_AUTH=false  # DANGER: Only for local development!
```

---

## Developer Onboarding

### Quick Start Guide

```markdown
# DevFlow Developer Setup - Secrets Configuration

## Step 1: Copy Environment Template

cd devflow
cp .env.example .env

## Step 2: Get Your AOSentry API Key

1. Go to https://aosentry.aocodex.ai
2. Sign in with your account
3. Navigate to API Keys
4. Create new key: "DevFlow Development"
5. Copy the key

## Step 3: Configure .env File

Edit `.env` and set:

AOSENTRY_API_KEY=your-aosentry-key-here

# Optional: 1Password (for enterprise users)
# OP_CONNECT_URL=http://localhost:8080
# OP_CONNECT_TOKEN=your-token-here

## Step 4: Generate Encryption Keys

# Generate secret encryption key
openssl rand -base64 32

# Add to .env
SECRET_ENCRYPTION_KEY=<generated-key>

# Generate session secret
openssl rand -hex 32

# Add to .env
SESSION_SECRET=<generated-secret>

## Step 5: Verify Configuration

npm run verify-secrets

## Step 6: Start Development

docker-compose up -d  # Start PostgreSQL + Qdrant
npm run dev           # Start DevFlow services

# Access local UI
open http://localhost:3737
```

---

## Security Best Practices

### .gitignore Configuration

```gitignore
# DevFlow .gitignore

# Environment files (NEVER commit these!)
.env
.env.local
.env.*.local
.env.development
.env.test
.env.staging
.env.production

# 1Password credentials
secrets/
1password-credentials.json

# Database files (local development)
*.db
*.sqlite
*.sqlite3

# Logs (may contain secrets)
logs/
*.log

# IDE settings (may contain paths to secrets)
.vscode/settings.json
.idea/workspace.xml
```

### Compliance

#### SOC 2 Compliance

- ✅ Encryption at rest (database, 1Password)
- ✅ Encryption in transit (HTTPS, TLS)
- ✅ Audit logging (all secret access)
- ✅ Access controls (RBAC)
- ✅ Secret rotation policies
- ✅ Incident response (rotation on breach)

#### HIPAA Compliance

- ✅ Encryption (AES-256)
- ✅ Access logging
- ✅ User authentication (OAuth)
- ✅ Data retention policies
- ✅ Breach notification procedures

#### GDPR Compliance

- ✅ Right to deletion (remove user secrets)
- ✅ Data portability (export secrets)
- ✅ Purpose limitation (secrets used only for DevFlow)
- ✅ Security by design (encryption default)

---

## Deployment Mode Specifics

### Local Development Mode

**Recommended Setup:**
- Use `.env` file for simplicity
- No 1Password required
- Secrets stay on your machine

```bash
# .env (local)
DEVFLOW_MODE=local
AOSENTRY_API_KEY=your-dev-key
DATABASE_URL=postgresql://devflow:devflow@localhost:5432/devflow
QDRANT_URL=http://localhost:6333
```

### SaaS Mode (devflow.aocodex.ai)

**Secrets Management:**
- DevFlow manages system secrets in 1Password
- Users only need AOSentry API key
- OAuth tokens encrypted in database
- Automatic secret rotation

```bash
# User .env (SaaS mode)
DEVFLOW_MODE=saas
DEVFLOW_API_KEY=your-saas-api-key
AOSENTRY_API_KEY=your-aosentry-key

# All other secrets managed by DevFlow platform
```

### On-Premise Mode

**Recommended Setup:**
- Deploy 1Password Connect Server
- Use 1Password for all secrets
- Team vault for shared secrets
- Individual vaults for user secrets

```bash
# .env (on-premise)
DEVFLOW_MODE=onprem
OP_CONNECT_URL=http://onepassword-connect:8080
OP_CONNECT_TOKEN=<service-account-token>

# All secrets resolved from 1Password
# No secrets in .env file!
```

---

## Success Metrics

### Security Metrics

| Metric | Target | Critical |
|--------|--------|----------|
| Secrets in 1Password (prod) | > 95% | Yes |
| Secret rotation compliance | > 90% | Yes |
| Failed rotation attempts | < 1% | Yes |
| Unauthorized access attempts | 0 | Yes |
| Secrets in git history | 0 | Yes |

### Operational Metrics

| Metric | Target | Critical |
|--------|--------|----------|
| Secret retrieval latency (p95) | < 100ms | No |
| 1Password availability | > 99.9% | Yes |
| Secret rotation success rate | > 99% | Yes |
| Time to rotate after expiry | < 24h | Yes |

---

## Future Enhancements

### Phase 1 (Q2 2026)
1. **Auto-rotation for API keys** - Automatic generation and rotation
2. **Secret sharing** - Temporary secret sharing with expiration
3. **Multi-region 1Password** - Geo-redundant secret storage
4. **Hardware security modules** - HSM integration for enterprise

### Phase 2 (Q3 2026)
1. **Secrets versioning** - Track secret history and rollback
2. **Dynamic secrets** - Generate secrets on-demand (database credentials)
3. **Secret dependencies** - Track which services use which secrets
4. **Automated breach response** - Auto-rotate on detected breach

---

**End of PRD-007**
