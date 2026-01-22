"""Tests for configuration loading."""

import os
from pathlib import Path

from devflow.core.config import (
    find_config_file,
    load_project_config,
    validate_config,
)


def test_find_config_file(mock_config: Path) -> None:
    """Test finding devflow.yml in current directory."""
    found = find_config_file()
    assert found is not None
    assert found.name == "devflow.yml"


def test_load_project_config(mock_config: Path) -> None:
    """Test loading and parsing configuration."""
    config = load_project_config()
    assert config is not None
    assert config.project.name == "test-project"
    assert config.version == "1"


def test_validate_config_valid(mock_config: Path) -> None:
    """Test validation of valid configuration."""
    errors = validate_config(mock_config)
    assert len(errors) == 0


def test_validate_config_invalid_yaml(temp_dir: Path) -> None:
    """Test validation with invalid YAML."""
    original_dir = os.getcwd()
    os.chdir(temp_dir)

    config_path = temp_dir / "devflow.yml"
    config_path.write_text("invalid: yaml: content: [")

    errors = validate_config(config_path)
    assert len(errors) > 0
    assert "YAML" in errors[0] or "parse" in errors[0].lower()

    os.chdir(original_dir)


def test_config_database_environments(mock_config: Path) -> None:
    """Test database environment configuration."""
    config = load_project_config()
    assert config is not None

    assert "local" in config.database.environments
    assert "staging" in config.database.environments

    local_env = config.database.environments["local"]
    assert local_env.url_env == "DATABASE_URL"

    staging_env = config.database.environments["staging"]
    assert staging_env.url_secret == "test_database_url"
    assert staging_env.host == "test-host"


def test_get_database_url_from_env(mock_config: Path) -> None:
    """Test getting database URL from environment variable."""
    os.environ["DATABASE_URL"] = "postgresql://localhost/test"

    config = load_project_config()
    assert config is not None

    url = config.get_database_url("local")
    assert url == "postgresql://localhost/test"

    # Clean up
    del os.environ["DATABASE_URL"]
