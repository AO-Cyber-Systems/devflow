"""Configuration loading and validation."""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field
from rich.console import Console

from devflow.core.errors import ConfigError

console = Console()


class DatabaseEnvConfig(BaseModel):
    """Database configuration for a specific environment."""

    url_env: Optional[str] = None  # Environment variable name for URL
    url_secret: Optional[str] = None  # Docker secret name for URL
    host: Optional[str] = None  # SSH host for remote connections
    ssh_user: Optional[str] = None
    direct_port: Optional[int] = None
    require_approval: bool = False


class MigrationsConfig(BaseModel):
    """Migration settings."""

    directory: str = "supabase/migrations"
    format: str = "sql"  # sql, supabase, prisma, alembic
    tracking_table: str = "schema_migrations"
    tracking_schema: str = "public"
    use_supabase_cli: bool = False  # Force Supabase CLI executor even with format: sql


class DatabaseConfig(BaseModel):
    """Database configuration."""

    migrations: MigrationsConfig = Field(default_factory=MigrationsConfig)
    environments: dict[str, DatabaseEnvConfig] = Field(default_factory=dict)


class SecretMapping(BaseModel):
    """Individual secret mapping."""

    name: str
    op_item: Optional[str] = None
    op_field: Optional[str] = None
    github_secret: Optional[str] = None
    docker_secret: Optional[str] = None


class SecretsConfig(BaseModel):
    """Secrets configuration."""

    provider: str = "1password"
    vault: str = "AOCyber"
    mappings: list[SecretMapping] = Field(default_factory=list)


class ServiceConfig(BaseModel):
    """Individual service configuration."""

    image: str
    stack: str
    replicas: int = 1
    health_endpoint: Optional[str] = None


class DeploymentEnvConfig(BaseModel):
    """Deployment configuration for a specific environment."""

    host: Optional[str] = None
    ssh_user: str = "deploy"
    ssh_key_secret: Optional[str] = None
    auto_deploy_branch: Optional[str] = None
    require_approval: bool = False
    approval_environment: Optional[str] = None


class DeploymentConfig(BaseModel):
    """Deployment configuration."""

    registry: str = "ghcr.io"
    organization: str = "ao-cyber-systems"
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

    domains: list[str] = Field(
        default_factory=lambda: ["*.localhost", "*.aocodex.localhost", "*.aosentry.localhost"]
    )
    cert_dir: str = "~/.devflow/certs"


class InfrastructureConfig(BaseModel):
    """Shared infrastructure configuration for local development."""

    enabled: bool = True
    network_name: str = "devflow-proxy"
    # Legacy network names to replace during compose transformation
    legacy_networks: list[str] = Field(default_factory=lambda: ["proxy", "aosentry-proxy"])
    traefik: TraefikConfig = Field(default_factory=TraefikConfig)
    certificates: CertificatesConfig = Field(default_factory=CertificatesConfig)


class ProjectConfig(BaseModel):
    """Project metadata."""

    name: str
    preset: Optional[str] = None


class DevflowConfig(BaseModel):
    """Main devflow configuration."""

    version: str = "1"
    project: ProjectConfig
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)
    development: DevelopmentConfig = Field(default_factory=DevelopmentConfig)
    infrastructure: InfrastructureConfig = Field(default_factory=InfrastructureConfig)

    def get_database_url(self, env: str) -> Optional[str]:
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


def find_config_file() -> Optional[Path]:
    """Find devflow.yml in current directory or parents."""
    current = Path.cwd()

    while current != current.parent:
        config_path = current / "devflow.yml"
        if config_path.exists():
            return config_path
        current = current.parent

    return None


def load_project_config() -> Optional[DevflowConfig]:
    """Load project configuration from devflow.yml."""
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


def initialize_project(preset: Optional[str] = None, force: bool = False) -> None:
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
        # Create default configuration
        config_content = f"""# Devflow Configuration
version: "1"

project:
  name: {project_name}

database:
  migrations:
    directory: supabase/migrations
    format: sql
    tracking_table: schema_migrations

  environments:
    local:
      url_env: DATABASE_URL
    staging:
      url_secret: {project_name}_database_url
      host: ao-staging-manager
      ssh_user: deploy
    production:
      url_secret: {project_name}_database_url
      require_approval: true

secrets:
  provider: 1password
  vault: AOCyber
  mappings: []

deployment:
  registry: ghcr.io
  organization: ao-cyber-systems
  services: {{}}
  environments:
    staging:
      host: ao-staging-manager
      ssh_user: deploy
    production:
      require_approval: true

development:
  compose_file: docker-compose.yml
  services: []
"""

    with open(config_path, "w") as f:
        f.write(config_content)

    console.print(f"[green]Created devflow.yml[/green]")
    console.print("\nNext steps:")
    console.print("  1. Edit devflow.yml to match your project")
    console.print("  2. Run 'devflow doctor' to verify your setup")
    console.print("  3. Run 'devflow db status' to check migrations")
