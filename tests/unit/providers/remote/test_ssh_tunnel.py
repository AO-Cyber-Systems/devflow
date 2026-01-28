"""Tests for SSH tunnel provider."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devflow.core.config import RemoteContextConfig, TunnelPortMapping
from devflow.providers.remote.ssh_tunnel import SSHTunnelProvider
from devflow.providers.remote.tunnel import TunnelStatus


@pytest.fixture
def remote_config() -> RemoteContextConfig:
    """Create a test remote context configuration."""
    return RemoteContextConfig(
        enabled=True,
        name="test-remote",
        host="192.168.1.100",
        user="developer",
        ssh_port=22,
        tunnels=[
            TunnelPortMapping(local=80, remote=80, description="HTTP"),
            TunnelPortMapping(local=443, remote=443, description="HTTPS"),
        ],
    )


@pytest.fixture
def tunnel_provider(remote_config: RemoteContextConfig) -> SSHTunnelProvider:
    """Create a test SSH tunnel provider."""
    return SSHTunnelProvider(remote_config)


class TestSSHTunnelProvider:
    """Tests for SSHTunnelProvider."""

    def test_init(self, tunnel_provider: SSHTunnelProvider, remote_config: RemoteContextConfig) -> None:
        """Test provider initialization."""
        assert tunnel_provider.config == remote_config
        assert tunnel_provider.config.host == "192.168.1.100"
        assert tunnel_provider.config.user == "developer"

    @patch("shutil.which")
    def test_is_available_with_ssh(self, mock_which: MagicMock, tunnel_provider: SSHTunnelProvider) -> None:
        """Test availability check when SSH is installed."""
        mock_which.return_value = "/usr/bin/ssh"
        assert tunnel_provider.is_available() is True
        mock_which.assert_called_with("ssh")

    @patch("shutil.which")
    def test_is_available_without_ssh(self, mock_which: MagicMock, tunnel_provider: SSHTunnelProvider) -> None:
        """Test availability check when SSH is not installed."""
        mock_which.return_value = None
        assert tunnel_provider.is_available() is False

    def test_build_tunnel_args(self, tunnel_provider: SSHTunnelProvider) -> None:
        """Test building SSH -L arguments."""
        args = tunnel_provider._build_tunnel_args()

        assert "-L" in args
        assert "80:localhost:80" in args
        assert "443:localhost:443" in args

    def test_build_ssh_opts(self, tunnel_provider: SSHTunnelProvider) -> None:
        """Test building SSH options."""
        opts = tunnel_provider._build_ssh_opts()

        assert "-o" in opts
        assert "ServerAliveInterval=30" in opts
        assert "ServerAliveCountMax=3" in opts
        assert "ExitOnForwardFailure=yes" in opts
        assert "BatchMode=yes" in opts
        assert "-p" in opts
        assert "22" in opts

    def test_build_ssh_opts_with_key(self, remote_config: RemoteContextConfig) -> None:
        """Test SSH options include key path when specified."""
        remote_config.ssh_key = Path("~/.ssh/id_ed25519")
        provider = SSHTunnelProvider(remote_config)
        opts = provider._build_ssh_opts()

        assert "-i" in opts

    @patch.object(SSHTunnelProvider, "_load_state")
    def test_health_stopped(self, mock_load: MagicMock, tunnel_provider: SSHTunnelProvider) -> None:
        """Test health check when tunnel is stopped."""
        mock_load.return_value = None

        health = tunnel_provider.health()
        assert health.status == TunnelStatus.STOPPED

    @patch.object(SSHTunnelProvider, "_load_state")
    @patch.object(SSHTunnelProvider, "_pid_exists")
    def test_health_dead_process(
        self, mock_pid: MagicMock, mock_load: MagicMock, tunnel_provider: SSHTunnelProvider
    ) -> None:
        """Test health check when tunnel process died."""
        mock_load.return_value = {"pid": 12345, "started_at": 0}
        mock_pid.return_value = False

        health = tunnel_provider.health()
        assert health.status == TunnelStatus.FAILED
        assert "died" in health.error.lower()

    @patch.object(SSHTunnelProvider, "_load_state")
    @patch.object(SSHTunnelProvider, "_pid_exists")
    @patch.object(SSHTunnelProvider, "_measure_latency")
    def test_health_running(
        self, mock_latency: MagicMock, mock_pid: MagicMock, mock_load: MagicMock, tunnel_provider: SSHTunnelProvider
    ) -> None:
        """Test health check when tunnel is running."""
        import time

        mock_load.return_value = {"pid": 12345, "started_at": time.time() - 60}
        mock_pid.return_value = True
        mock_latency.return_value = 5.5

        health = tunnel_provider.health()
        assert health.status == TunnelStatus.RUNNING
        assert health.pid == 12345
        assert health.latency_ms == 5.5

    @patch.object(SSHTunnelProvider, "_load_state")
    @patch.object(SSHTunnelProvider, "_pid_exists")
    @patch.object(SSHTunnelProvider, "_measure_latency")
    def test_health_reconnecting(
        self, mock_latency: MagicMock, mock_pid: MagicMock, mock_load: MagicMock, tunnel_provider: SSHTunnelProvider
    ) -> None:
        """Test health check when tunnel is unresponsive."""
        mock_load.return_value = {"pid": 12345, "started_at": 0}
        mock_pid.return_value = True
        mock_latency.return_value = None  # Connection failed

        health = tunnel_provider.health()
        assert health.status == TunnelStatus.RECONNECTING
        assert health.pid == 12345
        assert "unresponsive" in health.error.lower()

    def test_is_running_true(self, tunnel_provider: SSHTunnelProvider) -> None:
        """Test is_running when tunnel is running."""
        with patch.object(tunnel_provider, "health") as mock_health:
            mock_health.return_value = MagicMock(status=TunnelStatus.RUNNING)
            assert tunnel_provider.is_running() is True

    def test_is_running_false(self, tunnel_provider: SSHTunnelProvider) -> None:
        """Test is_running when tunnel is stopped."""
        with patch.object(tunnel_provider, "health") as mock_health:
            mock_health.return_value = MagicMock(status=TunnelStatus.STOPPED)
            assert tunnel_provider.is_running() is False

    def test_save_and_load_state(self, tunnel_provider: SSHTunnelProvider, tmp_path: Path) -> None:
        """Test saving and loading tunnel state."""
        # Override state file location
        tunnel_provider.STATE_FILE = tmp_path / "tunnel.json"

        # Save state
        tunnel_provider._save_state(12345)

        # Load state
        state = tunnel_provider._load_state()
        assert state is not None
        assert state["pid"] == 12345
        assert state["host"] == "192.168.1.100"
        assert state["user"] == "developer"
        assert "started_at" in state
        assert "tunnels" in state

    def test_clear_state(self, tunnel_provider: SSHTunnelProvider, tmp_path: Path) -> None:
        """Test clearing tunnel state."""
        # Override state file location
        state_file = tmp_path / "tunnel.json"
        tunnel_provider.STATE_FILE = state_file

        # Create state file
        state_file.write_text(json.dumps({"pid": 12345}))
        assert state_file.exists()

        # Clear state
        tunnel_provider._clear_state()
        assert not state_file.exists()

    @patch("os.kill")
    def test_pid_exists_true(self, mock_kill: MagicMock, tunnel_provider: SSHTunnelProvider) -> None:
        """Test PID exists check when process exists."""
        mock_kill.return_value = None
        assert tunnel_provider._pid_exists(12345) is True
        mock_kill.assert_called_with(12345, 0)

    @patch("os.kill")
    def test_pid_exists_false(self, mock_kill: MagicMock, tunnel_provider: SSHTunnelProvider) -> None:
        """Test PID exists check when process doesn't exist."""
        mock_kill.side_effect = ProcessLookupError()
        assert tunnel_provider._pid_exists(12345) is False

    def test_pid_exists_none(self, tunnel_provider: SSHTunnelProvider) -> None:
        """Test PID exists check with None PID."""
        assert tunnel_provider._pid_exists(None) is False

    @patch("subprocess.run")
    @patch.object(SSHTunnelProvider, "_find_tunnel_pid")
    @patch.object(SSHTunnelProvider, "is_running")
    @patch("time.sleep")
    def test_start_success(
        self,
        mock_sleep: MagicMock,
        mock_running: MagicMock,
        mock_find_pid: MagicMock,
        mock_run: MagicMock,
        tunnel_provider: SSHTunnelProvider,
        tmp_path: Path,
    ) -> None:
        """Test successful tunnel start."""
        tunnel_provider.STATE_FILE = tmp_path / "tunnel.json"
        mock_running.return_value = False
        mock_run.return_value = MagicMock(returncode=0)
        mock_find_pid.return_value = 12345

        tunnel_provider.start()

        assert mock_run.called
        mock_find_pid.assert_called_once()

    @patch.object(SSHTunnelProvider, "is_running")
    def test_start_already_running(self, mock_running: MagicMock, tunnel_provider: SSHTunnelProvider) -> None:
        """Test start when tunnel is already running."""
        mock_running.return_value = True

        # Should return without doing anything
        tunnel_provider.start()
        # No exception means success

    @patch("os.kill")
    @patch.object(SSHTunnelProvider, "_load_state")
    def test_stop(
        self, mock_load: MagicMock, mock_kill: MagicMock, tunnel_provider: SSHTunnelProvider, tmp_path: Path
    ) -> None:
        """Test stopping the tunnel."""
        tunnel_provider.STATE_FILE = tmp_path / "tunnel.json"
        mock_load.return_value = {"pid": 12345}

        tunnel_provider.stop()

        mock_kill.assert_called_with(12345, 15)  # SIGTERM = 15


class TestTunnelPortMapping:
    """Tests for TunnelPortMapping configuration."""

    def test_default_tunnels(self) -> None:
        """Test default tunnel port mappings."""
        config = RemoteContextConfig(enabled=True, host="test.example.com")

        # Check default tunnels
        assert len(config.tunnels) == 4
        assert config.tunnels[0].local == 80
        assert config.tunnels[0].remote == 80
        assert config.tunnels[0].description == "HTTP"
        assert config.tunnels[1].local == 443
        assert config.tunnels[1].remote == 443
        assert config.tunnels[2].local == 5432  # PostgreSQL
        assert config.tunnels[3].local == 6379  # Redis

    def test_custom_tunnels(self) -> None:
        """Test custom tunnel port mappings."""
        config = RemoteContextConfig(
            enabled=True,
            host="test.example.com",
            tunnels=[
                TunnelPortMapping(local=8080, remote=80, description="Custom HTTP"),
            ],
        )

        assert len(config.tunnels) == 1
        assert config.tunnels[0].local == 8080
        assert config.tunnels[0].remote == 80
