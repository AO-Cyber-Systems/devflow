"""Cross-platform tests for SSH provider."""

import os
from pathlib import Path
from unittest.mock import patch

from devflow.core.platform import Platform
from devflow.providers.ssh import SSHProvider


class TestSSHProviderSshDir:
    """Tests for SSH directory resolution across platforms."""

    def test_ssh_dir_on_linux(self) -> None:
        """Test SSH directory on Linux."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            provider = SSHProvider()
            ssh_dir = provider.get_ssh_dir()
            assert ssh_dir == Path.home() / ".ssh"

    def test_ssh_dir_on_macos(self) -> None:
        """Test SSH directory on macOS."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.MACOS):
            provider = SSHProvider()
            ssh_dir = provider.get_ssh_dir()
            assert ssh_dir == Path.home() / ".ssh"

    def test_ssh_dir_on_wsl2(self) -> None:
        """Test SSH directory on WSL2."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WSL2):
            provider = SSHProvider()
            ssh_dir = provider.get_ssh_dir()
            assert ssh_dir == Path.home() / ".ssh"

    def test_ssh_dir_on_windows(self) -> None:
        """Test SSH directory on Windows."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            with patch.dict(os.environ, {"USERPROFILE": "C:\\Users\\Test"}):
                provider = SSHProvider()
                ssh_dir = provider.get_ssh_dir()
                assert ssh_dir == Path("C:\\Users\\Test") / ".ssh"


class TestSSHProviderKeyPath:
    """Tests for SSH key path resolution."""

    def test_ssh_key_path_default(self) -> None:
        """Test SSH key path with default key name."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            provider = SSHProvider()
            key_path = provider.get_ssh_key_path()
            assert key_path == Path.home() / ".ssh" / "id_rsa"

    def test_ssh_key_path_custom_name(self) -> None:
        """Test SSH key path with custom key name."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            provider = SSHProvider()
            key_path = provider.get_ssh_key_path("id_ed25519")
            assert key_path == Path.home() / ".ssh" / "id_ed25519"

    def test_ssh_key_path_on_windows(self) -> None:
        """Test SSH key path on Windows."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            with patch.dict(os.environ, {"USERPROFILE": "C:\\Users\\Test"}):
                provider = SSHProvider()
                key_path = provider.get_ssh_key_path()
                assert key_path == Path("C:\\Users\\Test") / ".ssh" / "id_rsa"


class TestSSHProviderKnownHosts:
    """Tests for known_hosts path resolution."""

    def test_known_hosts_on_linux(self) -> None:
        """Test known_hosts path on Linux."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            provider = SSHProvider()
            known_hosts = provider.get_known_hosts_path()
            assert known_hosts == Path.home() / ".ssh" / "known_hosts"

    def test_known_hosts_on_windows(self) -> None:
        """Test known_hosts path on Windows."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            with patch.dict(os.environ, {"USERPROFILE": "C:\\Users\\Test"}):
                provider = SSHProvider()
                known_hosts = provider.get_known_hosts_path()
                assert known_hosts == Path("C:\\Users\\Test") / ".ssh" / "known_hosts"


class TestSSHProviderConfig:
    """Tests for SSH config path resolution."""

    def test_ssh_config_on_linux(self) -> None:
        """Test SSH config path on Linux."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            provider = SSHProvider()
            config = provider.get_ssh_config_path()
            assert config == Path.home() / ".ssh" / "config"

    def test_ssh_config_on_macos(self) -> None:
        """Test SSH config path on macOS."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.MACOS):
            provider = SSHProvider()
            config = provider.get_ssh_config_path()
            assert config == Path.home() / ".ssh" / "config"
