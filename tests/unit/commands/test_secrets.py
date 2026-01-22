"""Tests for secrets commands."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from devflow.commands.secrets import _get_repo_name, app

runner = CliRunner()


class TestGetRepoName:
    """Tests for _get_repo_name helper function."""

    @patch("subprocess.run")
    def test_get_repo_name_ssh_format(self, mock_run: MagicMock) -> None:
        """Test parsing SSH git URL format."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="git@github.com:org/repo.git\n",
        )

        result = _get_repo_name()
        assert result == "org/repo"

    @patch("subprocess.run")
    def test_get_repo_name_https_format(self, mock_run: MagicMock) -> None:
        """Test parsing HTTPS git URL format."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://github.com/org/repo.git\n",
        )

        result = _get_repo_name()
        assert result == "org/repo"

    @patch("subprocess.run")
    def test_get_repo_name_failure(self, mock_run: MagicMock) -> None:
        """Test get_repo_name when git command fails."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")

        result = _get_repo_name()
        assert result is None


class TestSecretsListCommand:
    """Tests for secrets list command."""

    def test_list_no_config(self, tmp_path: Path) -> None:
        """Test list command without devflow.yml."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = runner.invoke(app, ["list", "--json"])
            output = json.loads(result.output)
            assert output["success"] is False
            assert "devflow.yml" in output["error"]
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.load_project_config")
    @patch("devflow.providers.onepassword.OnePasswordProvider")
    def test_list_1password_success(
        self,
        mock_op_class: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test listing secrets from 1Password."""
        mock_config = MagicMock()
        mock_config.secrets.vault = "TestVault"
        mock_config.secrets.mappings = []
        mock_load_config.return_value = mock_config

        mock_op = MagicMock()
        mock_op.is_authenticated.return_value = True
        mock_op.list_items.return_value = [
            {"title": "secret1", "id": "id1", "category": "LOGIN"},
            {"title": "secret2", "id": "id2", "category": "PASSWORD"},
        ]
        mock_op_class.return_value = mock_op

        result = runner.invoke(app, ["list", "--source", "1password", "--json"])
        output = json.loads(result.output)

        assert output["success"] is True
        assert len(output["secrets"]) == 2

    @patch("devflow.core.config.load_project_config")
    @patch("devflow.providers.onepassword.OnePasswordProvider")
    def test_list_1password_not_authenticated(
        self,
        mock_op_class: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test listing when 1Password not authenticated."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_op = MagicMock()
        mock_op.is_authenticated.return_value = False
        mock_op_class.return_value = mock_op

        result = runner.invoke(app, ["list", "--source", "1password", "--json"])
        output = json.loads(result.output)

        assert output["success"] is False
        assert "authenticated" in output["error"].lower()


class TestSecretsSyncCommand:
    """Tests for secrets sync command."""

    @patch("devflow.core.config.load_project_config")
    def test_sync_no_mappings(self, mock_load_config: MagicMock) -> None:
        """Test sync when no mappings configured."""
        mock_config = MagicMock()
        mock_config.secrets.mappings = []
        mock_load_config.return_value = mock_config

        result = runner.invoke(app, ["sync", "--json"])
        output = json.loads(result.output)

        assert output["success"] is True
        assert output["synced"] == 0

    @patch("devflow.core.config.load_project_config")
    @patch("devflow.commands.secrets._get_repo_name")
    @patch("devflow.providers.onepassword.OnePasswordProvider")
    @patch("devflow.providers.github.GitHubProvider")
    def test_sync_dry_run(
        self,
        mock_gh_class: MagicMock,
        mock_op_class: MagicMock,
        mock_repo: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test sync dry run mode."""
        mock_mapping = MagicMock()
        mock_mapping.name = "TEST_SECRET"
        mock_mapping.op_item = "TestItem"
        mock_mapping.op_field = "password"
        mock_mapping.github_secret = "GITHUB_SECRET"
        mock_mapping.docker_secret = None

        mock_config = MagicMock()
        mock_config.secrets.vault = "TestVault"
        mock_config.secrets.mappings = [mock_mapping]
        mock_load_config.return_value = mock_config

        mock_op = MagicMock()
        mock_op.is_authenticated.return_value = True
        mock_op.read_field.return_value = "secret_value"
        mock_op_class.return_value = mock_op

        mock_gh = MagicMock()
        mock_gh.is_authenticated.return_value = True
        mock_gh_class.return_value = mock_gh

        mock_repo.return_value = "org/repo"

        result = runner.invoke(app, ["sync", "--dry-run", "--json"])
        output = json.loads(result.output)

        assert output["dry_run"] is True
        assert output["results"][0]["status"] == "would_sync"
        mock_gh.set_secret.assert_not_called()


class TestSecretsVerifyCommand:
    """Tests for secrets verify command."""

    @patch("devflow.core.config.load_project_config")
    def test_verify_no_mappings(self, mock_load_config: MagicMock) -> None:
        """Test verify when no mappings configured."""
        mock_config = MagicMock()
        mock_config.secrets.mappings = []
        mock_load_config.return_value = mock_config

        result = runner.invoke(app, ["verify", "--json"])
        output = json.loads(result.output)

        assert output["success"] is True
        assert output["verified"] == 0


class TestSecretsExportCommand:
    """Tests for secrets export command."""

    def test_export_non_local_env(self, tmp_path: Path) -> None:
        """Test export fails for non-local environments."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        # Create minimal config
        config_content = """
version: "1"
project:
  name: test
"""
        (tmp_path / "devflow.yml").write_text(config_content)

        try:
            result = runner.invoke(app, ["export", "--env", "production", "--json"])
            output = json.loads(result.output)
            assert output["success"] is False
            assert "local" in output["error"].lower()
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.load_project_config")
    @patch("devflow.providers.onepassword.OnePasswordProvider")
    def test_export_success(
        self,
        mock_op_class: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test successful export."""
        mock_mapping = MagicMock()
        mock_mapping.name = "database-url"
        mock_mapping.op_item = "TestItem"
        mock_mapping.op_field = "password"

        mock_config = MagicMock()
        mock_config.secrets.vault = "TestVault"
        mock_config.secrets.mappings = [mock_mapping]
        mock_load_config.return_value = mock_config

        mock_op = MagicMock()
        mock_op.is_authenticated.return_value = True
        mock_op.read_field.return_value = "postgres://localhost/db"
        mock_op_class.return_value = mock_op

        result = runner.invoke(app, ["export", "--env", "local", "--json"])
        output = json.loads(result.output)

        assert output["success"] is True
        assert output["exported"] == 1
