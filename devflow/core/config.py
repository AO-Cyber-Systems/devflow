"""Configuration loading and validation."""

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from rich.console import Console

from devflow.core.paths import get_devflow_home

console = Console()


# Use platform-aware path for DevFlow home directory
DEVFLOW_HOME = get_devflow_home()
GLOBAL_CONFIG_PATH = DEVFLOW_HOME / "config.yml"


# =============================================================================
# Global Configuration (user-wide settings)
# =============================================================================


class GlobalGitConfig(BaseModel):
    """Global git configuration."""

    user_name: str | None = None
    user_email: str | None = None
    co_author_enabled: bool = True
    co_author_name: str = "Claude"
    co_author_email: str = "noreply@anthropic.com"


class GlobalDefaultsConfig(BaseModel):
    """Default values for new projects."""

    secrets_provider: str | None = None  # 1password, env, or None
    network_name: str = "devflow-proxy"
    registry: str | None = None  # Default container registry


class GlobalInfrastructureConfig(BaseModel):
    """Global infrastructure preferences."""

    auto_start: bool = False  # Auto-start Traefik when running devflow commands
    traefik_http_port: int = 80
    traefik_https_port: int = 443
    traefik_dashboard_port: int = 8088


class GlobalConfig(BaseModel):
    """User-wide devflow configuration stored in ~/.devflow/config.yml."""

    version: str = "1"
    git: GlobalGitConfig = Field(default_factory=GlobalGitConfig)
    defaults: GlobalDefaultsConfig = Field(default_factory=GlobalDefaultsConfig)
    infrastructure: GlobalInfrastructureConfig = Field(default_factory=GlobalInfrastructureConfig)
    setup_completed: bool = False  # Track if initial setup wizard was run


def get_global_config_path() -> Path:
    """Get the path to the global config file."""
    return GLOBAL_CONFIG_PATH


def load_global_config() -> GlobalConfig:
    """Load global configuration from ~/.devflow/config.yml.

    Returns default config if file doesn't exist.
    """
    config_path = get_global_config_path()
    if not config_path.exists():
        return GlobalConfig()

    try:
        with open(config_path) as f:
            raw_config = yaml.safe_load(f)
        if raw_config is None:
            return GlobalConfig()
        return GlobalConfig(**raw_config)
    except (yaml.YAMLError, Exception):
        return GlobalConfig()


def save_global_config(config: GlobalConfig) -> bool:
    """Save global configuration to ~/.devflow/config.yml.

    Returns True on success, False on failure.
    """
    config_path = get_global_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, "w") as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)
        return True
    except OSError:
        return False


def is_devflow_initialized() -> bool:
    """Check if devflow has been initialized globally."""
    config_path = get_global_config_path()
    if not config_path.exists():
        return False
    config = load_global_config()
    return config.setup_completed


# =============================================================================
# Project Configuration (per-project settings)
# =============================================================================


class DatabaseEnvConfig(BaseModel):
    """Database configuration for a specific environment."""

    url_env: str | None = None  # Environment variable name for URL
    url_secret: str | None = None  # Docker secret name for URL
    host: str | None = None  # SSH host for remote connections
    ssh_user: str | None = None
    direct_port: int | None = None
    require_approval: bool = False


class MigrationsConfig(BaseModel):
    """Migration settings."""

    directory: str = "migrations"
    format: str = "sql"  # sql, supabase, prisma, alembic
    tracking_table: str = "schema_migrations"
    tracking_schema: str = "public"
    use_supabase_cli: bool = False  # Force Supabase CLI executor even with format: sql


class DatabaseConfig(BaseModel):
    """Database configuration."""

    migrations: MigrationsConfig = Field(default_factory=MigrationsConfig)
    environments: dict[str, DatabaseEnvConfig] = Field(default_factory=dict)


class GitUserConfig(BaseModel):
    """Git user configuration."""

    name: str | None = None
    email: str | None = None


class GitCoAuthorConfig(BaseModel):
    """Git co-author configuration for AI commits."""

    enabled: bool = True
    name: str = "Claude"
    email: str = "noreply@anthropic.com"


class GitConfig(BaseModel):
    """Git configuration."""

    user: GitUserConfig = Field(default_factory=GitUserConfig)
    co_author: GitCoAuthorConfig = Field(default_factory=GitCoAuthorConfig)


class SecretMapping(BaseModel):
    """Individual secret mapping."""

    name: str
    op_item: str | None = None
    op_field: str | None = None
    github_secret: str | None = None
    docker_secret: str | None = None


class GitHubAppConfig(BaseModel):
    """GitHub App authentication configuration.

    Supports op:// references for 1Password integration.
    Example:
        app_id: op://AOCyber-Infrastructure/GitHub-App/app_id
        installation_id: op://AOCyber-Infrastructure/GitHub-App/installation_id
        private_key: op://AOCyber-Infrastructure/GitHub-App/private_key
    """

    app_id: str  # GitHub App ID (can be op:// reference)
    installation_id: str  # Installation ID for the org (can be op:// reference)
    private_key: str  # PEM-encoded private key (can be op:// reference)


class GitHubConfig(BaseModel):
    """GitHub configuration."""

    auth: str = "cli"  # "cli" (default, uses gh CLI) or "app" (GitHub App)
    app: GitHubAppConfig | None = None  # Required if auth == "app"


class SecretsConfig(BaseModel):
    """Secrets configuration."""

    provider: str | None = None  # 1password, env, or None (disabled)
    vault: str | None = None  # For 1password provider
    github: GitHubConfig | None = None  # GitHub-specific configuration
    mappings: list[SecretMapping] = Field(default_factory=list)


class ServiceConfig(BaseModel):
    """Individual service configuration."""

    image: str
    stack: str
    replicas: int = 1
    health_endpoint: str | None = None


class DeploymentEnvConfig(BaseModel):
    """Deployment configuration for a specific environment."""

    host: str | None = None
    ssh_user: str = "deploy"
    ssh_key_secret: str | None = None
    auto_deploy_branch: str | None = None
    require_approval: bool = False
    approval_environment: str | None = None


class DeploymentConfig(BaseModel):
    """Deployment configuration."""

    registry: str | None = None  # e.g., ghcr.io, docker.io, etc.
    organization: str | None = None  # Registry organization/namespace
    services: dict[str, ServiceConfig] = Field(default_factory=dict)
    environments: dict[str, DeploymentEnvConfig] = Field(default_factory=dict)


class DevelopmentConfig(BaseModel):
    """Local development configuration."""

    compose_file: str = "docker-compose.yml"
    services: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    ports: dict[str, int] = Field(default_factory=dict)


class TraefikConfig(BaseModel):
    """Traefik configuration for shared infrastructure."""

    http_port: int = 80
    https_port: int = 443
    dashboard_port: int = 8088  # Avoid conflict with common services on 8080
    dashboard_enabled: bool = True
    log_level: str = "INFO"


class CertificatesConfig(BaseModel):
    """Certificate configuration for local TLS."""

    domains: list[str] = Field(default_factory=lambda: ["*.localhost"])
    cert_dir: str = "~/.devflow/certs"


class InfrastructureConfig(BaseModel):
    """Shared infrastructure configuration for local development."""

    enabled: bool = False  # Disabled by default - user opts in
    network_name: str = "devflow-proxy"
    # Legacy network names to replace during compose transformation
    legacy_networks: list[str] = Field(default_factory=list)
    traefik: TraefikConfig = Field(default_factory=TraefikConfig)
    certificates: CertificatesConfig = Field(default_factory=CertificatesConfig)


class ProjectConfig(BaseModel):
    """Project metadata."""

    name: str
    preset: str | None = None


class DevflowConfig(BaseModel):
    """Main devflow configuration."""

    version: str = "1"
    project: ProjectConfig
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    secrets: SecretsConfig | None = None  # Optional - only if using secrets management
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)
    development: DevelopmentConfig = Field(default_factory=DevelopmentConfig)
    infrastructure: InfrastructureConfig = Field(default_factory=InfrastructureConfig)
    git: GitConfig = Field(default_factory=GitConfig)

    def get_database_url(self, env: str) -> str | None:
        """Get database URL for the specified environment."""
        env_config = self.database.environments.get(env)
        if not env_config:
            return None

        # Try environment variable first
        if env_config.url_env:
            return os.environ.get(env_config.url_env)

        # Try docker secret
        if env_config.url_secret:
            secret_path = Path(f"/run/secrets/{env_config.url_secret}")
            if secret_path.exists():
                return secret_path.read_text().strip()

        return None


def find_config_file() -> Path | None:
    """Find devflow.yml in current directory or parents."""
    current = Path.cwd()

    while current != current.parent:
        config_path = current / "devflow.yml"
        if config_path.exists():
            return config_path
        current = current.parent

    return None


def load_project_config(project_path: Path | None = None) -> DevflowConfig | None:
    """Load project configuration from devflow.yml.

    Args:
        project_path: Optional path to the project directory. If provided,
                      looks for devflow.yml in that directory. Otherwise,
                      searches from current directory upward.

    Returns:
        DevflowConfig if found, None otherwise.
    """
    if project_path:
        config_path = Path(project_path) / "devflow.yml"
        if not config_path.exists():
            return None
    else:
        config_path = find_config_file()
        if not config_path:
            return None

    with open(config_path) as f:
        raw_config = yaml.safe_load(f)

    return DevflowConfig(**raw_config)


def validate_config(config_path: Path) -> list[str]:
    """Validate configuration file and return list of errors."""
    errors = []

    if not config_path.exists():
        return ["Configuration file not found"]

    try:
        with open(config_path) as f:
            raw_config = yaml.safe_load(f)

        # Try to parse with Pydantic
        DevflowConfig(**raw_config)

    except yaml.YAMLError as e:
        errors.append(f"YAML parse error: {e}")
    except Exception as e:
        errors.append(f"Validation error: {e}")

    return errors


def get_current_env() -> str:
    """Get the current environment from environment variable or default."""
    return os.environ.get("DEVFLOW_ENV", "local")


def set_current_env(env: str) -> None:
    """Set the current environment."""
    os.environ["DEVFLOW_ENV"] = env


def initialize_project(preset: str | None = None, force: bool = False) -> None:
    """Initialize devflow in the current project."""
    config_path = Path.cwd() / "devflow.yml"

    if config_path.exists() and not force:
        console.print("[yellow]devflow.yml already exists. Use --force to overwrite.[/yellow]")
        return

    # Determine project name from directory
    project_name = Path.cwd().name

    # Load preset if specified
    if preset:
        preset_path = Path(__file__).parent.parent.parent / "presets" / f"{preset}.yml"
        if preset_path.exists():
            with open(preset_path) as f:
                config_content = f.read()
            console.print(f"Using preset: [bold]{preset}[/bold]")
        else:
            console.print(f"[yellow]Preset '{preset}' not found. Using default configuration.[/yellow]")
            preset = None

    if not preset:
        # Create minimal default configuration
        config_content = f"""# Devflow Configuration
# Documentation: https://github.com/ao-cyber-systems/devflow
version: "1"

project:
  name: {project_name}

# Database configuration (optional)
database:
  migrations:
    directory: migrations
    format: sql  # sql, supabase, prisma, alembic

  environments:
    local:
      url_env: DATABASE_URL

# Local development
development:
  compose_file: docker-compose.yml

# Uncomment to enable shared infrastructure (Traefik proxy)
# infrastructure:
#   enabled: true

# Uncomment to configure secrets management
# secrets:
#   provider: 1password  # or: env
#   vault: MyVault
#   mappings: []

# Uncomment to configure deployment
# deployment:
#   registry: ghcr.io
#   organization: my-org
#   services: {{}}
#   environments:
#     staging:
#       host: staging.example.com
#     production:
#       require_approval: true
"""

    with open(config_path, "w") as f:
        f.write(config_content)

    console.print("[green]Created devflow.yml[/green]")
    console.print("\nNext steps:")
    console.print("  1. Edit devflow.yml to match your project")
    console.print("  2. Run 'devflow doctor' to verify your setup")
    console.print("  3. Run 'devflow db status' to check migrations")
