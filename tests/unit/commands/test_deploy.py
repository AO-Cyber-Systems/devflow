"""Tests for deploy commands."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from devflow.commands.deploy import app, _get_env_config, _build_image_tag


runner = CliRunner()


class TestHelperFunctions:
    """Tests for deploy helper functions."""

    def test_get_env_config(self) -> None:
        """Test getting environment config."""
        mock_config = MagicMock()
        mock_config.deployment.environments = {
            "staging": MagicMock(host="staging.example.com"),
            "production": MagicMock(host="prod.example.com"),
        }

        result = _get_env_config(mock_config, "staging")
        assert result.host == "staging.example.com"

        result = _get_env_config(mock_config, "unknown")
        assert result is None

    def test_build_image_tag(self) -> None:
        """Test building image tag."""
        mock_config = MagicMock()
        mock_config.deployment.registry = "ghcr.io"
        mock_config.deployment.organization = "test-org"

        mock_service = MagicMock()
        mock_service.image = "my-service:latest"

        result = _build_image_tag(mock_config, "service", mock_service)
        assert result == "ghcr.io/test-org/my-service:latest"


class TestDeployStatusCommand:
    """Tests for deploy status command."""

    def test_status_no_config(self, tmp_path: Path) -> None:
        """Test status command without devflow.yml."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = runner.invoke(app, ["status", "--json"])
            output = json.loads(result.output)
            assert output["success"] is False
            assert "devflow.yml" in output["error"]
        finally:
            os.chdir(original_dir)

    @patch("devflow.core.config.load_project_config")
    def test_status_no_env_config(self, mock_load_config: MagicMock) -> None:
        """Test status when environment not configured."""
        mock_config = MagicMock()
        mock_config.deployment.environments = {}
        mock_load_config.return_value = mock_config

        result = runner.invoke(app, ["status", "--env", "unknown", "--json"])
        output = json.loads(result.output)

        assert output["success"] is False
        assert "unknown" in output["error"]

    @patch("devflow.core.config.load_project_config")
    @patch("devflow.providers.ssh.SSHProvider.is_available")
    @patch("devflow.providers.ssh.SSHProvider.execute")
    def test_status_remote_success(
        self,
        mock_execute: MagicMock,
        mock_available: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test status for remote environment."""
        mock_env = MagicMock()
        mock_env.host = "staging.example.com"
        mock_env.ssh_user = "deploy"

        mock_config = MagicMock()
        mock_config.deployment.environments = {"staging": mock_env}
        mock_load_config.return_value = mock_config

        mock_available.return_value = True

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = '{"Name":"api","Mode":"replicated","Replicas":"1/1","Image":"api:latest"}\n'
        mock_execute.return_value = mock_result

        result = runner.invoke(app, ["status", "--env", "staging", "--json"])
        output = json.loads(result.output)

        assert output["success"] is True
        assert len(output["services"]) == 1


class TestDeployStagingCommand:
    """Tests for deploy staging command."""

    @patch("devflow.core.config.load_project_config")
    def test_staging_no_services(self, mock_load_config: MagicMock) -> None:
        """Test staging deploy when no services configured."""
        mock_env = MagicMock()
        mock_env.host = "staging.example.com"
        mock_env.ssh_user = "deploy"
        mock_env.require_approval = False

        mock_config = MagicMock()
        mock_config.deployment.environments = {"staging": mock_env}
        mock_config.deployment.services = {}
        mock_load_config.return_value = mock_config

        result = runner.invoke(app, ["staging", "--json"])
        output = json.loads(result.output)

        assert output["success"] is True
        assert output["deployed"] == 0

    @patch("devflow.core.config.load_project_config")
    @patch("devflow.providers.ssh.SSHProvider.is_available")
    def test_staging_dry_run(
        self,
        mock_available: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test staging deploy dry run."""
        mock_env = MagicMock()
        mock_env.host = "staging.example.com"
        mock_env.ssh_user = "deploy"
        mock_env.require_approval = False

        mock_service = MagicMock()
        mock_service.image = "api:latest"
        mock_service.stack = "mystack"

        mock_config = MagicMock()
        mock_config.deployment.registry = "ghcr.io"
        mock_config.deployment.organization = "test-org"
        mock_config.deployment.environments = {"staging": mock_env}
        mock_config.deployment.services = {"api": mock_service}
        mock_load_config.return_value = mock_config

        mock_available.return_value = True

        result = runner.invoke(app, ["staging", "--dry-run", "--json"])
        output = json.loads(result.output)

        assert output["success"] is True
        assert output["dry_run"] is True
        assert output["results"][0]["status"] == "would_deploy"


class TestDeployProductionCommand:
    """Tests for deploy production command."""

    @patch("devflow.core.config.load_project_config")
    def test_production_require_approval(self, mock_load_config: MagicMock) -> None:
        """Test production deploy when approval required."""
        mock_env = MagicMock()
        mock_env.host = "prod.example.com"
        mock_env.ssh_user = "deploy"
        mock_env.require_approval = True

        mock_config = MagicMock()
        mock_config.deployment.environments = {"production": mock_env}
        mock_load_config.return_value = mock_config

        result = runner.invoke(app, ["production", "--yes", "--json"])
        output = json.loads(result.output)

        assert output["success"] is False
        assert "approval" in output["error"].lower()


class TestDeployRollbackCommand:
    """Tests for deploy rollback command."""

    @patch("devflow.core.config.load_project_config")
    @patch("devflow.providers.ssh.SSHProvider.is_available")
    @patch("devflow.providers.ssh.SSHProvider.execute")
    def test_rollback_success(
        self,
        mock_execute: MagicMock,
        mock_available: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test successful rollback."""
        mock_env = MagicMock()
        mock_env.host = "staging.example.com"
        mock_env.ssh_user = "deploy"

        mock_service = MagicMock()
        mock_service.stack = "mystack"

        mock_config = MagicMock()
        mock_config.deployment.environments = {"staging": mock_env}
        mock_config.deployment.services = {"api": mock_service}
        mock_load_config.return_value = mock_config

        mock_available.return_value = True

        mock_result = MagicMock()
        mock_result.success = True
        mock_execute.return_value = mock_result

        result = runner.invoke(app, ["rollback", "--env", "staging", "--json"])
        output = json.loads(result.output)

        assert output["success"] is True
        assert output["rolled_back"] == 1


class TestDeployLogsCommand:
    """Tests for deploy logs command."""

    @patch("devflow.core.config.load_project_config")
    @patch("devflow.providers.ssh.SSHProvider.is_available")
    @patch("devflow.providers.ssh.SSHProvider.execute")
    def test_logs_success(
        self,
        mock_execute: MagicMock,
        mock_available: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test getting logs successfully."""
        mock_env = MagicMock()
        mock_env.host = "staging.example.com"
        mock_env.ssh_user = "deploy"

        mock_config = MagicMock()
        mock_config.deployment.environments = {"staging": mock_env}
        mock_config.deployment.services = {}
        mock_load_config.return_value = mock_config

        mock_available.return_value = True

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "log line 1\nlog line 2\n"
        mock_execute.return_value = mock_result

        result = runner.invoke(app, ["logs", "myservice", "--env", "staging", "--json"])
        output = json.loads(result.output)

        assert output["success"] is True
        assert "log line" in output["logs"]


class TestDeploySSHCommand:
    """Tests for deploy ssh command."""

    @patch("devflow.core.config.load_project_config")
    def test_ssh_no_host(self, mock_load_config: MagicMock) -> None:
        """Test SSH when no host configured."""
        mock_env = MagicMock()
        mock_env.host = None

        mock_config = MagicMock()
        mock_config.deployment.environments = {"local": mock_env}
        mock_load_config.return_value = mock_config

        result = runner.invoke(app, ["ssh", "--env", "local", "--json"])
        output = json.loads(result.output)

        assert output["success"] is False
        assert "host" in output["error"].lower()
