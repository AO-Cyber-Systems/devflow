"""Tests for Docker context manager."""

import json
from unittest.mock import MagicMock, patch

import pytest

from devflow.core.config import RemoteContextConfig
from devflow.providers.remote.context import DockerContext, DockerContextManager


class TestDockerContext:
    """Tests for DockerContext dataclass."""

    def test_local_context(self) -> None:
        """Test a local Docker context."""
        ctx = DockerContext(
            name="default",
            description="Default Docker context",
            docker_endpoint="unix:///var/run/docker.sock",
            is_current=True,
        )
        assert ctx.name == "default"
        assert ctx.is_current is True
        assert ctx.is_devflow_context() is False

    def test_devflow_context(self) -> None:
        """Test a DevFlow-managed context."""
        ctx = DockerContext(
            name="devflow-dev-server",
            description="DevFlow remote: dev-server",
            docker_endpoint="ssh://user@192.168.1.100",
            is_current=False,
        )
        assert ctx.name == "devflow-dev-server"
        assert ctx.is_devflow_context() is True

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        ctx = DockerContext(
            name="devflow-test",
            description="Test context",
            docker_endpoint="ssh://user@host",
            is_current=True,
        )
        result = ctx.to_dict()

        assert result["name"] == "devflow-test"
        assert result["description"] == "Test context"
        assert result["docker_endpoint"] == "ssh://user@host"
        assert result["is_current"] is True
        assert result["is_devflow"] is True


class TestDockerContextManager:
    """Tests for DockerContextManager."""

    def test_init_without_config(self) -> None:
        """Test initialization without config."""
        manager = DockerContextManager()
        assert manager.config is None

    def test_init_with_config(self) -> None:
        """Test initialization with config."""
        config = RemoteContextConfig(enabled=True, host="example.com")
        manager = DockerContextManager(config)
        assert manager.config == config

    @patch("subprocess.run")
    def test_list_contexts(self, mock_run: MagicMock) -> None:
        """Test listing Docker contexts."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(
                {"Name": "default", "Description": "Default", "DockerEndpoint": "unix://", "Current": True}
            )
            + "\n"
            + json.dumps(
                {"Name": "devflow-remote", "Description": "Remote", "DockerEndpoint": "ssh://user@host", "Current": False}
            ),
        )

        manager = DockerContextManager()
        contexts = manager.list_contexts()

        assert len(contexts) == 2
        assert contexts[0].name == "default"
        assert contexts[0].is_current is True
        assert contexts[1].name == "devflow-remote"
        assert contexts[1].is_devflow_context() is True

    @patch("subprocess.run")
    def test_list_contexts_empty(self, mock_run: MagicMock) -> None:
        """Test listing contexts when docker fails."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "docker")

        manager = DockerContextManager()
        contexts = manager.list_contexts()

        assert contexts == []

    @patch("subprocess.run")
    def test_create_remote_context(self, mock_run: MagicMock) -> None:
        """Test creating a remote Docker context."""
        mock_run.return_value = MagicMock(returncode=0)

        config = RemoteContextConfig(
            enabled=True,
            host="192.168.1.100",
            user="developer",
            ssh_port=22,
        )
        manager = DockerContextManager(config)
        success, message = manager.create_remote_context("test", config)

        assert success is True
        assert "devflow-test" in message

        # Verify docker context create was called
        calls = mock_run.call_args_list
        create_call = None
        for call in calls:
            if "create" in call[0][0]:
                create_call = call
                break

        assert create_call is not None

    @patch("subprocess.run")
    def test_create_remote_context_custom_port(self, mock_run: MagicMock) -> None:
        """Test creating context with custom SSH port."""
        mock_run.return_value = MagicMock(returncode=0)

        config = RemoteContextConfig(
            enabled=True,
            host="192.168.1.100",
            user="developer",
            ssh_port=2222,
        )
        manager = DockerContextManager(config)
        success, message = manager.create_remote_context("test", config)

        assert success is True

    @patch("subprocess.run")
    def test_delete_context(self, mock_run: MagicMock) -> None:
        """Test deleting a Docker context."""
        # Mock list_contexts for current context check
        mock_run.side_effect = [
            MagicMock(
                returncode=0,
                stdout=json.dumps({"Name": "default", "Current": True}),
            ),
            MagicMock(returncode=0),  # delete
        ]

        manager = DockerContextManager()
        success, message = manager.delete_context("devflow-test")

        assert success is True

    @patch("subprocess.run")
    def test_use_context(self, mock_run: MagicMock) -> None:
        """Test switching Docker context."""
        mock_run.return_value = MagicMock(returncode=0)

        manager = DockerContextManager()
        success, message = manager.use_context("devflow-remote")

        assert success is True
        mock_run.assert_called()

    @patch("subprocess.run")
    def test_use_local(self, mock_run: MagicMock) -> None:
        """Test switching to local context."""
        mock_run.return_value = MagicMock(returncode=0)

        manager = DockerContextManager()
        success, message = manager.use_local()

        assert success is True
        # Should call docker context use default
        call_args = mock_run.call_args[0][0]
        assert "docker" in call_args
        assert "context" in call_args
        assert "use" in call_args
        assert "default" in call_args

    @patch("subprocess.run")
    def test_current_context(self, mock_run: MagicMock) -> None:
        """Test getting current context."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"Name": "default", "Current": True}),
        )

        manager = DockerContextManager()
        current = manager.current_context()

        assert current is not None
        assert current.name == "default"
        assert current.is_current is True

    @patch("subprocess.run")
    def test_is_remote_true(self, mock_run: MagicMock) -> None:
        """Test is_remote when using DevFlow context."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"Name": "devflow-remote", "Current": True}),
        )

        manager = DockerContextManager()
        assert manager.is_remote() is True

    @patch("subprocess.run")
    def test_is_remote_false(self, mock_run: MagicMock) -> None:
        """Test is_remote when using local context."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"Name": "default", "Current": True}),
        )

        manager = DockerContextManager()
        assert manager.is_remote() is False

    @patch("subprocess.run")
    def test_get_devflow_contexts(self, mock_run: MagicMock) -> None:
        """Test getting only DevFlow-managed contexts."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"Name": "default", "Current": True})
            + "\n"
            + json.dumps({"Name": "devflow-remote", "Current": False})
            + "\n"
            + json.dumps({"Name": "other", "Current": False}),
        )

        manager = DockerContextManager()
        devflow_contexts = manager.get_devflow_contexts()

        assert len(devflow_contexts) == 1
        assert devflow_contexts[0].name == "devflow-remote"

    @patch("subprocess.run")
    def test_test_connection_success(self, mock_run: MagicMock) -> None:
        """Test connection testing success."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="24.0.7\n",
        )

        manager = DockerContextManager()
        success, message = manager.test_connection()

        assert success is True
        assert "24.0.7" in message

    @patch("subprocess.run")
    def test_test_connection_failure(self, mock_run: MagicMock) -> None:
        """Test connection testing failure."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "docker", stderr="Connection refused")

        manager = DockerContextManager()
        success, message = manager.test_connection()

        assert success is False
        assert "failed" in message.lower()

    @patch("subprocess.run")
    def test_test_connection_timeout(self, mock_run: MagicMock) -> None:
        """Test connection testing timeout."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("docker", 30)

        manager = DockerContextManager()
        success, message = manager.test_connection()

        assert success is False
        assert "timed out" in message.lower()
