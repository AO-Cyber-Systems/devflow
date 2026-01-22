"""Tests for configuration loading."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from devflow.core.config import (
    GitHubAppConfig,
    GitHubConfig,
    GlobalConfig,
    SecretsConfig,
    find_config_file,
    is_devflow_initialized,
    load_global_config,
    load_project_config,
    save_global_config,
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


# =============================================================================
# Global Configuration Tests
# =============================================================================


class TestGlobalConfig:
    """Tests for global configuration."""

    def test_default_global_config(self) -> None:
        """Test default GlobalConfig values."""
        config = GlobalConfig()

        assert config.version == "1"
        assert config.setup_completed is False
        assert config.git.user_name is None
        assert config.git.user_email is None
        assert config.git.co_author_enabled is True
        assert config.git.co_author_name == "Claude"
        assert config.defaults.secrets_provider is None
        assert config.defaults.network_name == "devflow-proxy"
        assert config.infrastructure.auto_start is False

    def test_load_global_config_no_file(self, tmp_path: Path) -> None:
        """Test loading global config when file doesn't exist."""
        with patch("devflow.core.config.GLOBAL_CONFIG_PATH", tmp_path / "config.yml"):
            config = load_global_config()

        assert config.setup_completed is False
        assert config.git.user_name is None

    def test_load_global_config_with_file(self, tmp_path: Path) -> None:
        """Test loading global config from file."""
        config_file = tmp_path / "config.yml"
        config_file.write_text(
            """
version: "1"
git:
  user_name: "Test User"
  user_email: "test@example.com"
  co_author_enabled: false
setup_completed: true
"""
        )

        with patch("devflow.core.config.GLOBAL_CONFIG_PATH", config_file):
            config = load_global_config()

        assert config.setup_completed is True
        assert config.git.user_name == "Test User"
        assert config.git.user_email == "test@example.com"
        assert config.git.co_author_enabled is False

    def test_save_global_config(self, tmp_path: Path) -> None:
        """Test saving global config to file."""
        config_file = tmp_path / "config.yml"

        config = GlobalConfig()
        config.git.user_name = "Save Test"
        config.git.user_email = "save@example.com"
        config.setup_completed = True

        with patch("devflow.core.config.GLOBAL_CONFIG_PATH", config_file):
            result = save_global_config(config)

        assert result is True
        assert config_file.exists()

        # Verify content
        content = config_file.read_text()
        assert "Save Test" in content
        assert "save@example.com" in content
        assert "setup_completed: true" in content

    def test_is_devflow_initialized_false(self, tmp_path: Path) -> None:
        """Test is_devflow_initialized when not initialized."""
        with patch("devflow.core.config.GLOBAL_CONFIG_PATH", tmp_path / "nonexistent.yml"):
            assert is_devflow_initialized() is False

    def test_is_devflow_initialized_incomplete(self, tmp_path: Path) -> None:
        """Test is_devflow_initialized when setup not completed."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("setup_completed: false\n")

        with patch("devflow.core.config.GLOBAL_CONFIG_PATH", config_file):
            assert is_devflow_initialized() is False

    def test_is_devflow_initialized_complete(self, tmp_path: Path) -> None:
        """Test is_devflow_initialized when setup is completed."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("setup_completed: true\n")

        with patch("devflow.core.config.GLOBAL_CONFIG_PATH", config_file):
            assert is_devflow_initialized() is True

    def test_load_global_config_invalid_yaml(self, tmp_path: Path) -> None:
        """Test loading global config with invalid YAML returns default."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("invalid: yaml: [")

        with patch("devflow.core.config.GLOBAL_CONFIG_PATH", config_file):
            config = load_global_config()

        # Should return default config on error
        assert config.setup_completed is False

    def test_load_global_config_empty_file(self, tmp_path: Path) -> None:
        """Test loading global config with empty file returns default."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("")

        with patch("devflow.core.config.GLOBAL_CONFIG_PATH", config_file):
            config = load_global_config()

        # Should return default config on empty file
        assert config.setup_completed is False


# =============================================================================
# GitHub App Configuration Tests
# =============================================================================


class TestGitHubAppConfig:
    """Tests for GitHub App configuration model."""

    def test_github_app_config_basic(self) -> None:
        """Test basic GitHubAppConfig creation."""
        config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key="-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----",
        )
        assert config.app_id == "12345"
        assert config.installation_id == "67890"
        assert "PRIVATE KEY" in config.private_key

    def test_github_app_config_with_op_references(self) -> None:
        """Test GitHubAppConfig with 1Password references."""
        config = GitHubAppConfig(
            app_id="op://vault/item/app_id",
            installation_id="op://vault/item/installation_id",
            private_key="op://vault/item/private_key",
        )
        assert config.app_id.startswith("op://")
        assert config.installation_id.startswith("op://")
        assert config.private_key.startswith("op://")

    def test_github_app_config_missing_required_field(self) -> None:
        """Test that GitHubAppConfig requires all fields."""
        with pytest.raises(Exception):  # Pydantic validation error
            GitHubAppConfig(app_id="12345", installation_id="67890")  # type: ignore[call-arg]


class TestGitHubConfig:
    """Tests for GitHub configuration model."""

    def test_github_config_default_auth(self) -> None:
        """Test GitHubConfig default auth method."""
        config = GitHubConfig()
        assert config.auth == "cli"
        assert config.app is None

    def test_github_config_cli_auth(self) -> None:
        """Test GitHubConfig with CLI auth."""
        config = GitHubConfig(auth="cli")
        assert config.auth == "cli"

    def test_github_config_app_auth(self) -> None:
        """Test GitHubConfig with App auth."""
        app_config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key="test_key",
        )
        config = GitHubConfig(auth="app", app=app_config)
        assert config.auth == "app"
        assert config.app is not None
        assert config.app.app_id == "12345"


class TestSecretsConfigWithGitHub:
    """Tests for SecretsConfig with GitHub configuration."""

    def test_secrets_config_without_github(self) -> None:
        """Test SecretsConfig without GitHub configuration."""
        config = SecretsConfig(
            provider="1password",
            vault="TestVault",
        )
        assert config.github is None

    def test_secrets_config_with_github_cli(self) -> None:
        """Test SecretsConfig with GitHub CLI auth."""
        config = SecretsConfig(
            provider="1password",
            vault="TestVault",
            github=GitHubConfig(auth="cli"),
        )
        assert config.github is not None
        assert config.github.auth == "cli"

    def test_secrets_config_with_github_app(self) -> None:
        """Test SecretsConfig with GitHub App auth."""
        app_config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key="test_key",
        )
        github_config = GitHubConfig(auth="app", app=app_config)
        config = SecretsConfig(
            provider="1password",
            vault="TestVault",
            github=github_config,
        )
        assert config.github is not None
        assert config.github.auth == "app"
        assert config.github.app is not None
        assert config.github.app.app_id == "12345"
