"""Migration file generator."""

from datetime import datetime, timezone
from pathlib import Path

from devflow.core.config import DevflowConfig


def generate_migration_name(description: str) -> str:
    """Generate a migration filename with timestamp prefix."""
    # Format: YYYYMMDDHHMMSS_description.sql
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    # Clean description: lowercase, replace spaces with underscores
    clean_desc = description.lower().replace(" ", "_").replace("-", "_")
    # Remove any non-alphanumeric characters except underscores
    clean_desc = "".join(c for c in clean_desc if c.isalnum() or c == "_")
    return f"{timestamp}_{clean_desc}.sql"


def create_migration(config: DevflowConfig, description: str) -> Path:
    """Create a new migration file."""
    migrations_dir = Path(config.database.migrations.directory)

    # Ensure directory exists
    migrations_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    filename = generate_migration_name(description)
    filepath = migrations_dir / filename

    # Create migration file with template
    template = f"""-- Migration: {description}
-- Created: {datetime.now(timezone.utc).isoformat()}
-- Devflow migration file

-- Write your migration SQL here


-- Note: If you need a down migration, create a separate file with _down suffix
-- or use the rollback command to generate one
"""

    filepath.write_text(template)
    return filepath


def create_down_migration(config: DevflowConfig, up_migration: str) -> Path:
    """Create a down migration file for an existing up migration."""
    migrations_dir = Path(config.database.migrations.directory)
    up_path = migrations_dir / up_migration

    if not up_path.exists():
        raise FileNotFoundError(f"Up migration not found: {up_migration}")

    # Generate down migration filename
    down_filename = up_migration.replace(".sql", "_down.sql")
    down_path = migrations_dir / down_filename

    template = f"""-- Down migration for: {up_migration}
-- Created: {datetime.now(timezone.utc).isoformat()}
-- Devflow migration file

-- Write your rollback SQL here
-- This should reverse the changes made in {up_migration}


"""

    down_path.write_text(template)
    return down_path
