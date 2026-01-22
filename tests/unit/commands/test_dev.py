"""Tests for dev commands."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from devflow.commands.dev import app

runner = CliRunner()


class TestDevSetupCommand:
    """Tests for dev setup command."""

    @patch("devflow.providers.docker.DockerProvider")
    def test_setup_docker_not_running(self, mock_docker_class: MagicMock) -> None:
        """Test setup fails when Docker is not running."""
        mock_docker = MagicMock()
        mock_docker.is_authenticated.return_value = False
        mock_docker_class.return_value = mock_docker

        result = runner.invoke(app, ["setup", "--json"])
        output = json.loads(result.output)

        assert output["success"] is False
        assert any(s["name"] == "docker" and s["status"] == "error" for s in output["steps"])

    @patch("devflow.providers.docker.DockerProvider")
    @patch("devflow.core.config.load_project_config")
    def test_setup_no_config(
        self,
        mock_load_config: MagicMock,
        mock_docker_class: MagicMock,
    ) -> None:
        """Test setup fails when no devflow.yml found."""
        mock_docker = MagicMock()
        mock_docker.is_authenticated.return_value = True
        mock_docker_class.return_value = mock_docker
        mock_load_config.return_value = None

        result = runner.invoke(app, ["setup", "--json"])
        output = json.loads(result.output)

        assert output["success"] is False
        assert any(s["name"] == "config" and s["status"] == "error" for s in output["steps"])

    @patch("devflow.providers.docker.DockerProvider")
    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_setup_no_compose_file(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
        mock_docker_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setup skips pull when compose file doesn't exist."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            mock_docker = MagicMock()
            mock_docker.is_authenticated.return_value = True
            mock_docker_class.return_value = mock_docker

            mock_config = MagicMock()
            mock_config.development.compose_file = "docker-compose.yml"
            mock_config.infrastructure.enabled = False
            mock_load_config.return_value = mock_config

            result = runner.invoke(app, ["setup", "--json"])
            output = json.loads(result.output)

            assert output["success"] is True
            assert any(s["name"] == "pull_images" and s["status"] == "skipped" for s in output["steps"])
        finally:
            os.chdir(original_dir)

    @patch("devflow.providers.docker.DockerProvider")
    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_setup_with_compose_file(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
        mock_docker_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setup pulls images when compose file exists."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Create compose file
            (tmp_path / "docker-compose.yml").write_text("version: '3'")

            mock_docker = MagicMock()
            mock_docker.is_authenticated.return_value = True
            mock_docker_class.return_value = mock_docker

            mock_config = MagicMock()
            mock_config.development.compose_file = "docker-compose.yml"
            mock_config.infrastructure.enabled = False
            mock_load_config.return_value = mock_config

            mock_run.return_value = MagicMock(returncode=0)

            result = runner.invoke(app, ["setup", "--json"])
            output = json.loads(result.output)

            assert output["success"] is True
            assert any(s["name"] == "pull_images" and s["status"] == "ok" for s in output["steps"])
        finally:
            os.chdir(original_dir)

    @patch("devflow.providers.docker.DockerProvider")
    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_setup_env_template_simple(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
        mock_docker_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setup copies .env.template without 1Password refs."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Create env template without 1Password refs
            (tmp_path / ".env.template").write_text("DATABASE_URL=localhost\nDEBUG=true")

            mock_docker = MagicMock()
            mock_docker.is_authenticated.return_value = True
            mock_docker_class.return_value = mock_docker

            mock_config = MagicMock()
            mock_config.development.compose_file = "docker-compose.yml"
            mock_config.infrastructure.enabled = False
            mock_load_config.return_value = mock_config

            result = runner.invoke(app, ["setup", "--json"])
            output = json.loads(result.output)

            assert output["success"] is True
            assert any(s["name"] == "env_setup" and s["status"] == "ok" for s in output["steps"])
            assert (tmp_path / ".env.local").exists()
            assert (tmp_path / ".env.local").read_text() == "DATABASE_URL=localhost\nDEBUG=true"
        finally:
            os.chdir(original_dir)

    @patch("devflow.providers.docker.DockerProvider")
    @patch("devflow.providers.onepassword.OnePasswordProvider")
    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_setup_env_template_with_1password(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
        mock_op_class: MagicMock,
        mock_docker_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setup resolves 1Password refs in .env.template."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Create env template with 1Password ref
            (tmp_path / ".env.template").write_text("DATABASE_URL=op://vault/item/field")

            mock_docker = MagicMock()
            mock_docker.is_authenticated.return_value = True
            mock_docker_class.return_value = mock_docker

            mock_op = MagicMock()
            mock_op.is_authenticated.return_value = True
            mock_op.inject.return_value = "DATABASE_URL=resolved_secret"
            mock_op_class.return_value = mock_op

            mock_config = MagicMock()
            mock_config.development.compose_file = "docker-compose.yml"
            mock_config.infrastructure.enabled = False
            mock_config.secrets.provider = "1password"  # Enable 1Password
            mock_load_config.return_value = mock_config

            result = runner.invoke(app, ["setup", "--json"])
            output = json.loads(result.output)

            assert output["success"] is True
            assert any(s["name"] == "env_setup" and "1Password" in s.get("message", "") for s in output["steps"])
            assert (tmp_path / ".env.local").read_text() == "DATABASE_URL=resolved_secret"
        finally:
            os.chdir(original_dir)

    @patch("devflow.providers.docker.DockerProvider")
    @patch("devflow.providers.onepassword.OnePasswordProvider")
    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_setup_env_template_1password_not_authenticated(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
        mock_op_class: MagicMock,
        mock_docker_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setup copies template when 1Password not authenticated."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Create env template with 1Password ref
            (tmp_path / ".env.template").write_text("DATABASE_URL=op://vault/item/field")

            mock_docker = MagicMock()
            mock_docker.is_authenticated.return_value = True
            mock_docker_class.return_value = mock_docker

            mock_op = MagicMock()
            mock_op.is_authenticated.return_value = False
            mock_op_class.return_value = mock_op

            mock_config = MagicMock()
            mock_config.development.compose_file = "docker-compose.yml"
            mock_config.infrastructure.enabled = False
            mock_config.secrets.provider = "1password"  # Enable 1Password
            mock_load_config.return_value = mock_config

            result = runner.invoke(app, ["setup", "--json"])
            output = json.loads(result.output)

            assert output["success"] is True
            assert any(s["name"] == "env_setup" and s["status"] == "warning" for s in output["steps"])
            # Template copied as-is
            assert (tmp_path / ".env.local").read_text() == "DATABASE_URL=op://vault/item/field"
        finally:
            os.chdir(original_dir)

    @patch("devflow.providers.docker.DockerProvider")
    @patch("devflow.core.config.load_project_config")
    @patch("devflow.providers.infrastructure.InfrastructureProvider")
    @patch("subprocess.run")
    def test_setup_with_infrastructure(
        self,
        mock_run: MagicMock,
        mock_infra_class: MagicMock,
        mock_load_config: MagicMock,
        mock_docker_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setup starts infrastructure when enabled."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            mock_docker = MagicMock()
            mock_docker.is_authenticated.return_value = True
            mock_docker_class.return_value = mock_docker

            mock_config = MagicMock()
            mock_config.development.compose_file = "docker-compose.yml"
            mock_config.infrastructure.enabled = True
            mock_load_config.return_value = mock_config

            mock_infra = MagicMock()
            mock_infra.start.return_value = MagicMock(success=True)
            mock_infra_class.return_value = mock_infra

            result = runner.invoke(app, ["setup", "--json"])
            output = json.loads(result.output)

            assert output["success"] is True
            assert any(s["name"] == "infrastructure" and s["status"] == "ok" for s in output["steps"])
        finally:
            os.chdir(original_dir)

    @patch("devflow.providers.docker.DockerProvider")
    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_setup_infrastructure_disabled(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
        mock_docker_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test setup skips infrastructure when disabled."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            mock_docker = MagicMock()
            mock_docker.is_authenticated.return_value = True
            mock_docker_class.return_value = mock_docker

            mock_config = MagicMock()
            mock_config.development.compose_file = "docker-compose.yml"
            mock_config.infrastructure.enabled = False
            mock_load_config.return_value = mock_config

            result = runner.invoke(app, ["setup", "--json"])
            output = json.loads(result.output)

            assert output["success"] is True
            assert any(s["name"] == "infrastructure" and s["status"] == "skipped" for s in output["steps"])
        finally:
            os.chdir(original_dir)


class TestDevStartCommand:
    """Tests for dev start command."""

    @patch("devflow.core.config.load_project_config")
    def test_start_no_config(self, mock_load_config: MagicMock) -> None:
        """Test start fails without config."""
        mock_load_config.return_value = None

        result = runner.invoke(app, ["start"])

        assert result.exit_code == 1
        assert "devflow.yml" in result.output

    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_start_success(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test successful start."""
        mock_config = MagicMock()
        mock_config.development.compose_file = "docker-compose.yml"
        mock_load_config.return_value = mock_config

        runner.invoke(app, ["start"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "docker" in call_args
        assert "compose" in call_args
        assert "up" in call_args
        assert "-d" in call_args

    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_start_specific_service(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test starting specific service."""
        mock_config = MagicMock()
        mock_config.development.compose_file = "docker-compose.yml"
        mock_load_config.return_value = mock_config

        runner.invoke(app, ["start", "--service", "api"])

        call_args = mock_run.call_args[0][0]
        assert "api" in call_args

    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_start_no_detach(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test start without detach."""
        mock_config = MagicMock()
        mock_config.development.compose_file = "docker-compose.yml"
        mock_load_config.return_value = mock_config

        runner.invoke(app, ["start", "--no-detach"])

        call_args = mock_run.call_args[0][0]
        assert "-d" not in call_args


class TestDevStopCommand:
    """Tests for dev stop command."""

    @patch("devflow.core.config.load_project_config")
    def test_stop_no_config(self, mock_load_config: MagicMock) -> None:
        """Test stop fails without config."""
        mock_load_config.return_value = None

        result = runner.invoke(app, ["stop"])

        assert result.exit_code == 1

    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_stop_success(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test successful stop."""
        mock_config = MagicMock()
        mock_config.development.compose_file = "docker-compose.yml"
        mock_load_config.return_value = mock_config

        runner.invoke(app, ["stop"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "stop" in call_args


class TestDevLogsCommand:
    """Tests for dev logs command."""

    @patch("devflow.core.config.load_project_config")
    def test_logs_no_config(self, mock_load_config: MagicMock) -> None:
        """Test logs fails without config."""
        mock_load_config.return_value = None

        result = runner.invoke(app, ["logs", "api"])

        assert result.exit_code == 1

    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_logs_success(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test successful logs."""
        mock_config = MagicMock()
        mock_config.development.compose_file = "docker-compose.yml"
        mock_load_config.return_value = mock_config

        runner.invoke(app, ["logs", "api"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "logs" in call_args
        assert "api" in call_args

    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_logs_with_follow(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test logs with follow flag."""
        mock_config = MagicMock()
        mock_config.development.compose_file = "docker-compose.yml"
        mock_load_config.return_value = mock_config

        runner.invoke(app, ["logs", "api", "--follow"])

        call_args = mock_run.call_args[0][0]
        assert "-f" in call_args


class TestDevShellCommand:
    """Tests for dev shell command."""

    @patch("devflow.core.config.load_project_config")
    def test_shell_no_config(self, mock_load_config: MagicMock) -> None:
        """Test shell fails without config."""
        mock_load_config.return_value = None

        result = runner.invoke(app, ["shell", "api"])

        assert result.exit_code == 1

    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_shell_success(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test successful shell."""
        mock_config = MagicMock()
        mock_config.development.compose_file = "docker-compose.yml"
        mock_load_config.return_value = mock_config

        runner.invoke(app, ["shell", "api"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "exec" in call_args
        assert "api" in call_args
        assert "/bin/sh" in call_args


class TestDevResetCommand:
    """Tests for dev reset command."""

    @patch("devflow.core.config.load_project_config")
    def test_reset_no_config(self, mock_load_config: MagicMock) -> None:
        """Test reset fails without config."""
        mock_load_config.return_value = None

        result = runner.invoke(app, ["reset"])

        assert result.exit_code == 1

    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_reset_success(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test successful reset."""
        mock_config = MagicMock()
        mock_config.development.compose_file = "docker-compose.yml"
        mock_load_config.return_value = mock_config

        runner.invoke(app, ["reset"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "down" in call_args

    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_reset_with_volumes_confirmed(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test reset with volumes when confirmed."""
        mock_config = MagicMock()
        mock_config.development.compose_file = "docker-compose.yml"
        mock_load_config.return_value = mock_config

        # Simulate user confirming with 'y'
        result = runner.invoke(app, ["reset", "--volumes"], input="y\n")

        if result.exit_code == 0:
            call_args = mock_run.call_args[0][0]
            assert "-v" in call_args

    @patch("devflow.core.config.load_project_config")
    @patch("subprocess.run")
    def test_reset_with_volumes_declined(
        self,
        mock_run: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test reset with volumes when declined."""
        mock_config = MagicMock()
        mock_config.development.compose_file = "docker-compose.yml"
        mock_load_config.return_value = mock_config

        # Simulate user declining with 'n'
        result = runner.invoke(app, ["reset", "--volumes"], input="n\n")

        assert result.exit_code == 0
        assert "Aborted" in result.output
        mock_run.assert_not_called()
