"""Tests for SSH provider."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devflow.providers.ssh import SSHProvider, SSHResult, SSHTunnel


class TestSSHProvider:
    """Tests for SSH provider."""

    def test_name_and_binary(self) -> None:
        """Test provider name and binary."""
        provider = SSHProvider()
        assert provider.name == "ssh"
        assert provider.binary == "ssh"

    @patch("shutil.which")
    def test_is_available_when_installed(self, mock_which: MagicMock) -> None:
        """Test availability when SSH is installed."""
        mock_which.return_value = "/usr/bin/ssh"
        provider = SSHProvider()
        assert provider.is_available() is True

    @patch("shutil.which")
    def test_is_available_when_not_installed(self, mock_which: MagicMock) -> None:
        """Test availability when SSH is not installed."""
        mock_which.return_value = None
        provider = SSHProvider()
        assert provider.is_available() is False

    def test_is_authenticated_same_as_available(self) -> None:
        """Test that is_authenticated returns same as is_available for SSH."""
        provider = SSHProvider()
        with patch.object(provider, "is_available", return_value=True):
            assert provider.is_authenticated() is True
        with patch.object(provider, "is_available", return_value=False):
            assert provider.is_authenticated() is False

    @patch("subprocess.run")
    def test_execute_success(self, mock_run: MagicMock) -> None:
        """Test successful SSH command execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="command output",
            stderr="",
        )

        provider = SSHProvider()
        result = provider.execute("host", "user", "echo test")

        assert result.success is True
        assert result.stdout == "command output"
        assert result.exit_code == 0

    @patch("subprocess.run")
    def test_execute_failure(self, mock_run: MagicMock) -> None:
        """Test failed SSH command execution."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Connection refused",
        )

        provider = SSHProvider()
        result = provider.execute("host", "user", "echo test")

        assert result.success is False
        assert "Connection refused" in result.stderr
        assert result.exit_code == 1

    @patch("subprocess.run")
    def test_execute_timeout(self, mock_run: MagicMock) -> None:
        """Test SSH command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=60)

        provider = SSHProvider()
        result = provider.execute("host", "user", "echo test", timeout=60)

        assert result.success is False
        assert "timed out" in result.stderr.lower()
        assert result.exit_code == -1

    @patch("subprocess.run")
    def test_execute_with_key_path(self, mock_run: MagicMock) -> None:
        """Test SSH execution with custom key path."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="success",
            stderr="",
        )

        provider = SSHProvider()
        provider.execute("host", "user", "echo test", key_path="/path/to/key")

        # Verify -i flag was passed
        call_args = mock_run.call_args[0][0]
        assert "-i" in call_args
        assert "/path/to/key" in call_args

    @patch("subprocess.Popen")
    def test_create_tunnel_success(self, mock_popen: MagicMock) -> None:
        """Test successful SSH tunnel creation."""
        # Simulate tunnel staying open (wait returns TimeoutExpired)
        mock_process = MagicMock()
        mock_process.wait.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=2)
        mock_process.poll.return_value = None  # Process still running
        mock_popen.return_value = mock_process

        provider = SSHProvider()
        tunnel = provider.create_tunnel(
            local_port=5432,
            remote_host="localhost",
            remote_port=5432,
            ssh_host="bastion.example.com",
            ssh_user="user",
        )

        assert tunnel is not None
        assert tunnel.local_port == 5432
        assert tunnel.remote_host == "localhost"
        assert tunnel.remote_port == 5432

    @patch("subprocess.Popen")
    def test_create_tunnel_failure(self, mock_popen: MagicMock) -> None:
        """Test failed SSH tunnel creation."""
        # Simulate tunnel failing immediately
        mock_process = MagicMock()
        mock_process.wait.return_value = 1  # Process exited
        mock_popen.return_value = mock_process

        provider = SSHProvider()
        tunnel = provider.create_tunnel(
            local_port=5432,
            remote_host="localhost",
            remote_port=5432,
            ssh_host="bastion.example.com",
            ssh_user="user",
        )

        assert tunnel is None

    @patch("subprocess.Popen")
    def test_connect_returns_process(self, mock_popen: MagicMock) -> None:
        """Test interactive SSH connection."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        provider = SSHProvider()
        process = provider.connect("host", "user")

        assert process is mock_process
        # Verify user@host format
        call_args = mock_popen.call_args[0][0]
        assert "user@host" in call_args

    def test_write_temp_key(self, tmp_path: Path) -> None:
        """Test writing SSH key to temp file."""
        provider = SSHProvider()
        key_content = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest\n-----END OPENSSH PRIVATE KEY-----"

        key_path = provider.write_temp_key(key_content)

        try:
            assert Path(key_path).exists()
            assert Path(key_path).read_text() == key_content
            # Check permissions (0o600)
            import stat
            mode = stat.S_IMODE(Path(key_path).stat().st_mode)
            assert mode == 0o600
        finally:
            SSHProvider.cleanup_temp_key(key_path)

    def test_cleanup_temp_key(self, tmp_path: Path) -> None:
        """Test cleaning up temp key file."""
        key_file = tmp_path / "test_key"
        key_file.write_text("key content")

        SSHProvider.cleanup_temp_key(str(key_file))

        assert not key_file.exists()

    def test_cleanup_temp_key_nonexistent(self, tmp_path: Path) -> None:
        """Test cleaning up nonexistent key file doesn't raise."""
        # Should not raise
        SSHProvider.cleanup_temp_key(str(tmp_path / "nonexistent"))

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_copy_to_remote_success(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Test successful SCP copy."""
        mock_which.return_value = "/usr/bin/scp"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        provider = SSHProvider()
        result = provider.copy_to_remote(
            local_path="/local/file.txt",
            remote_path="/remote/file.txt",
            host="host",
            user="user",
        )

        assert result.success is True

    @patch("shutil.which")
    def test_copy_to_remote_no_scp(self, mock_which: MagicMock) -> None:
        """Test SCP when scp is not installed."""
        mock_which.return_value = None

        provider = SSHProvider()
        result = provider.copy_to_remote(
            local_path="/local/file.txt",
            remote_path="/remote/file.txt",
            host="host",
            user="user",
        )

        assert result.success is False
        assert "not found" in result.stderr.lower()


class TestSSHResult:
    """Tests for SSHResult dataclass."""

    def test_ssh_result_success(self) -> None:
        """Test successful SSHResult."""
        result = SSHResult(
            success=True,
            stdout="output",
            stderr="",
            exit_code=0,
        )
        assert result.success is True
        assert result.stdout == "output"
        assert result.exit_code == 0

    def test_ssh_result_failure(self) -> None:
        """Test failed SSHResult."""
        result = SSHResult(
            success=False,
            stdout="",
            stderr="error message",
            exit_code=1,
        )
        assert result.success is False
        assert result.stderr == "error message"
        assert result.exit_code == 1


class TestSSHTunnel:
    """Tests for SSHTunnel dataclass."""

    def test_tunnel_is_active(self) -> None:
        """Test tunnel is_active when process running."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process running

        tunnel = SSHTunnel(
            local_port=5432,
            remote_host="localhost",
            remote_port=5432,
            process=mock_process,
        )

        assert tunnel.is_active() is True

    def test_tunnel_is_not_active(self) -> None:
        """Test tunnel is_active when process exited."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Process exited

        tunnel = SSHTunnel(
            local_port=5432,
            remote_host="localhost",
            remote_port=5432,
            process=mock_process,
        )

        assert tunnel.is_active() is False

    def test_tunnel_close(self) -> None:
        """Test closing tunnel."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process running

        tunnel = SSHTunnel(
            local_port=5432,
            remote_host="localhost",
            remote_port=5432,
            process=mock_process,
        )

        tunnel.close()

        mock_process.terminate.assert_called_once()
