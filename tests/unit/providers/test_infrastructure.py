"""Tests for infrastructure provider."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from devflow.core.config import InfrastructureConfig
from devflow.providers.infrastructure import (
    InfraResult,
    InfraStatus,
    InfrastructureProvider,
    RegisteredProject,
)


class TestInfraStatus:
    """Tests for InfraStatus dataclass."""

    def test_default_values(self) -> None:
        """Test default status values."""
        status = InfraStatus()
        assert status.network_exists is False
        assert status.network_name == ""
        assert status.traefik_running is False
        assert status.traefik_container_id is None
        assert status.certificates_valid is False
        assert status.registered_projects == []

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        status = InfraStatus(
            network_exists=True,
            network_name="devflow-proxy",
            traefik_running=True,
        )
        result = status.to_dict()

        assert result["network_exists"] is True
        assert result["network_name"] == "devflow-proxy"
        assert result["traefik_running"] is True


class TestInfraResult:
    """Tests for InfraResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful result."""
        result = InfraResult(success=True, message="Operation completed")
        assert result.success is True
        assert result.message == "Operation completed"
        assert result.details == {}

    def test_failure_result(self) -> None:
        """Test failure result."""
        result = InfraResult(success=False, message="Operation failed", details={"error": "test"})
        assert result.success is False
        assert result.message == "Operation failed"
        assert result.details == {"error": "test"}


class TestInfrastructureProvider:
    """Tests for InfrastructureProvider."""

    def test_default_config(self) -> None:
        """Test provider with default config."""
        provider = InfrastructureProvider()
        assert provider.config.network_name == "devflow-proxy"
        assert provider.config.enabled is True

    def test_custom_config(self) -> None:
        """Test provider with custom config."""
        config = InfrastructureConfig(
            network_name="custom-network",
            enabled=False,
        )
        provider = InfrastructureProvider(config)
        assert provider.config.network_name == "custom-network"
        assert provider.config.enabled is False

    def test_infrastructure_dir(self) -> None:
        """Test infrastructure directory path."""
        provider = InfrastructureProvider()
        assert provider.infrastructure_dir == Path.home() / ".devflow" / "infrastructure"

    def test_certs_dir(self) -> None:
        """Test certificates directory path."""
        provider = InfrastructureProvider()
        assert provider.certs_dir == Path.home() / ".devflow" / "certs"

    def test_projects_file(self) -> None:
        """Test projects file path."""
        provider = InfrastructureProvider()
        assert provider.projects_file == Path.home() / ".devflow" / "projects.json"

    @patch.object(InfrastructureProvider, "_network_exists")
    @patch.object(InfrastructureProvider, "_is_traefik_running")
    def test_status(
        self,
        mock_traefik: MagicMock,
        mock_network: MagicMock,
    ) -> None:
        """Test status retrieval."""
        mock_network.return_value = True
        mock_traefik.return_value = False

        provider = InfrastructureProvider()
        with patch.object(provider.mkcert, "cert_exists", return_value=True):
            status = provider.status()

        assert status.network_exists is True
        assert status.traefik_running is False
        assert status.certificates_valid is True

    @patch("subprocess.run")
    def test_network_exists_true(self, mock_run: MagicMock) -> None:
        """Test network exists check when network exists."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="devflow-proxy\n",
        )

        provider = InfrastructureProvider()
        result = provider._network_exists()

        assert result is True

    @patch("subprocess.run")
    def test_network_exists_false(self, mock_run: MagicMock) -> None:
        """Test network exists check when network doesn't exist."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="\n",
        )

        provider = InfrastructureProvider()
        result = provider._network_exists()

        assert result is False

    @patch("subprocess.run")
    def test_is_traefik_running_true(self, mock_run: MagicMock) -> None:
        """Test Traefik running check when running."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="devflow-traefik\n",
        )

        provider = InfrastructureProvider()
        result = provider._is_traefik_running()

        assert result is True

    @patch("subprocess.run")
    def test_is_traefik_running_false(self, mock_run: MagicMock) -> None:
        """Test Traefik running check when not running."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="\n",
        )

        provider = InfrastructureProvider()
        result = provider._is_traefik_running()

        assert result is False

    @patch("subprocess.run")
    def test_create_network_success(self, mock_run: MagicMock) -> None:
        """Test successful network creation."""
        # First call for exists check returns empty (doesn't exist)
        # Second call creates the network
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=""),  # network doesn't exist
            MagicMock(returncode=0),  # network created
        ]

        provider = InfrastructureProvider()
        result = provider.create_network()

        assert result.success is True

    @patch("subprocess.run")
    def test_create_network_already_exists(self, mock_run: MagicMock) -> None:
        """Test network creation when network already exists."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="devflow-proxy\n",
        )

        provider = InfrastructureProvider()
        result = provider.create_network()

        assert result.success is True
        assert "already exists" in result.message.lower()

    def test_doctor_output(self) -> None:
        """Test doctor diagnostics output."""
        provider = InfrastructureProvider()
        with patch.object(provider, "_network_exists", return_value=True):
            with patch.object(provider, "_is_traefik_running", return_value=False):
                with patch.object(provider.mkcert, "cert_exists", return_value=True):
                    diagnostics = provider.doctor()

        assert "docker" in diagnostics
        assert "mkcert" in diagnostics
        assert "infrastructure" in diagnostics
        assert diagnostics["infrastructure"]["network_exists"] is True
        assert diagnostics["infrastructure"]["traefik_running"] is False
        assert diagnostics["infrastructure"]["certificates_exist"] is True


class TestProjectRegistry:
    """Tests for project registry functionality."""

    def test_get_registered_projects_empty(self, tmp_path: Path) -> None:
        """Test getting projects when no registry exists."""
        provider = InfrastructureProvider()
        # Override projects file to non-existent path
        provider.DEVFLOW_HOME = tmp_path

        projects = provider.get_registered_projects()
        assert projects == []

    def test_get_registered_projects_with_data(self, tmp_path: Path) -> None:
        """Test getting projects from registry."""
        provider = InfrastructureProvider()
        provider.DEVFLOW_HOME = tmp_path

        # Create a projects file
        projects_file = tmp_path / "projects.json"
        projects_file.write_text(
            json.dumps(
                {
                    "projects": [
                        {
                            "name": "test-project",
                            "path": "/path/to/project",
                            "domains": ["test.localhost"],
                            "compose_files": ["docker-compose.yml"],
                            "configured_at": "2024-01-01T00:00:00",
                            "backup_path": None,
                        }
                    ]
                }
            )
        )

        projects = provider.get_registered_projects()
        assert len(projects) == 1
        assert projects[0].name == "test-project"
        assert projects[0].path == "/path/to/project"

    def test_register_project(self, tmp_path: Path) -> None:
        """Test registering a new project."""
        provider = InfrastructureProvider()
        provider.DEVFLOW_HOME = tmp_path

        project = RegisteredProject(
            name="new-project",
            path="/path/to/new",
            domains=["new.localhost"],
            compose_files=["docker-compose.yml"],
            configured_at="2024-01-01T00:00:00",
        )

        result = provider.register_project(project)
        assert result.success is True

        # Verify it was saved
        projects = provider.get_registered_projects()
        assert len(projects) == 1
        assert projects[0].name == "new-project"

    def test_unregister_project(self, tmp_path: Path) -> None:
        """Test unregistering a project."""
        provider = InfrastructureProvider()
        provider.DEVFLOW_HOME = tmp_path

        # First register a project
        project = RegisteredProject(
            name="to-remove",
            path="/path/to/remove",
            domains=[],
            compose_files=[],
            configured_at="2024-01-01T00:00:00",
        )
        provider.register_project(project)

        # Then unregister it
        result = provider.unregister_project("/path/to/remove")
        assert result.success is True

        # Verify it was removed
        projects = provider.get_registered_projects()
        assert len(projects) == 0

    def test_unregister_nonexistent_project(self, tmp_path: Path) -> None:
        """Test unregistering a project that doesn't exist."""
        provider = InfrastructureProvider()
        provider.DEVFLOW_HOME = tmp_path

        result = provider.unregister_project("/nonexistent/path")
        assert result.success is False
        assert "not found" in result.message.lower()


class TestHostsManagement:
    """Tests for /etc/hosts management."""

    def test_get_hosts_entries_empty(self) -> None:
        """Test getting hosts entries when none exist."""
        provider = InfrastructureProvider()

        # Mock reading hosts file without devflow section
        with patch(
            "builtins.open",
            MagicMock(
                return_value=MagicMock(
                    __enter__=lambda s: MagicMock(readlines=lambda: ["127.0.0.1 localhost\n"]),
                    __exit__=lambda s, *args: None,
                )
            ),
        ):
            entries = provider.get_hosts_entries()

        assert entries == []

    def test_get_hosts_entries_with_data(self) -> None:
        """Test getting hosts entries when they exist."""
        provider = InfrastructureProvider()

        hosts_content = [
            "127.0.0.1 localhost\n",
            "# devflow-managed-start\n",
            "127.0.0.1 traefik.localhost\n",
            "127.0.0.1 aocodex.localhost\n",
            "# devflow-managed-end\n",
        ]

        with patch(
            "builtins.open",
            MagicMock(
                return_value=MagicMock(
                    __enter__=lambda s: MagicMock(readlines=lambda: hosts_content),
                    __exit__=lambda s, *args: None,
                )
            ),
        ):
            entries = provider.get_hosts_entries()

        assert len(entries) == 2
        assert "127.0.0.1 traefik.localhost" in entries
        assert "127.0.0.1 aocodex.localhost" in entries
