"""Tests for migration functionality."""

from pathlib import Path

import pytest

from devflow.core.config import load_project_config
from devflow.migrations.generator import create_migration, generate_migration_name
from devflow.migrations.tracker import MigrationTracker


def test_generate_migration_name() -> None:
    """Test migration filename generation."""
    name = generate_migration_name("add user preferences")

    # Should start with timestamp
    assert len(name.split("_")[0]) == 14  # YYYYMMDDHHMMSS

    # Should contain cleaned description
    assert "add_user_preferences" in name

    # Should end with .sql
    assert name.endswith(".sql")


def test_generate_migration_name_special_chars() -> None:
    """Test migration name with special characters."""
    name = generate_migration_name("add user's email--address")

    # Should strip special characters
    assert "'" not in name
    assert "--" not in name


def test_migration_tracker_local_migrations(mock_config: Path, migrations_dir: Path) -> None:
    """Test getting local migration files."""
    config = load_project_config()
    assert config is not None

    tracker = MigrationTracker(config, "local")
    migrations = tracker.get_local_migrations()

    assert len(migrations) == 3
    assert "20240101000000_initial.sql" in migrations
    assert "20240102000000_add_email.sql" in migrations
    assert "20240103000000_add_index.sql" in migrations


def test_migration_tracker_compute_checksum(migrations_dir: Path) -> None:
    """Test migration checksum computation."""
    migration_path = migrations_dir / "20240101000000_initial.sql"

    checksum = MigrationTracker.compute_checksum(migration_path)

    # SHA-256 produces 64 character hex string
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)

    # Same file should produce same checksum
    checksum2 = MigrationTracker.compute_checksum(migration_path)
    assert checksum == checksum2


def test_create_migration(mock_config: Path, migrations_dir: Path) -> None:
    """Test creating a new migration file."""
    config = load_project_config()
    assert config is not None

    filepath = create_migration(config, "add user settings")

    assert filepath.exists()
    assert "add_user_settings" in filepath.name
    assert filepath.suffix == ".sql"

    content = filepath.read_text()
    assert "Migration: add user settings" in content
