"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_dir: Path) -> Path:
    """Create a mock devflow.yml configuration."""
    config_content = """
version: "1"

project:
  name: test-project

database:
  migrations:
    directory: supabase/migrations
    format: sql
    tracking_table: schema_migrations

  environments:
    local:
      url_env: DATABASE_URL
    staging:
      url_secret: test_database_url
      host: test-host
      ssh_user: deploy

secrets:
  provider: 1password
  vault: Test

deployment:
  registry: ghcr.io
  organization: test-org

development:
  compose_file: docker-compose.yml
"""
    config_path = temp_dir / "devflow.yml"
    config_path.write_text(config_content)

    # Change to temp directory for tests
    original_dir = os.getcwd()
    os.chdir(temp_dir)

    yield config_path

    os.chdir(original_dir)


@pytest.fixture
def migrations_dir(temp_dir: Path) -> Path:
    """Create a mock migrations directory."""
    migrations = temp_dir / "supabase" / "migrations"
    migrations.mkdir(parents=True)

    # Create some test migration files
    (migrations / "20240101000000_initial.sql").write_text("CREATE TABLE users (id SERIAL PRIMARY KEY);")
    (migrations / "20240102000000_add_email.sql").write_text("ALTER TABLE users ADD COLUMN email TEXT;")
    (migrations / "20240103000000_add_index.sql").write_text("CREATE INDEX idx_users_email ON users(email);")

    return migrations
