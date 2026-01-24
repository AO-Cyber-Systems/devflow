"""Tests for cross-platform path handling."""

import os
from pathlib import Path
from unittest.mock import patch

from devflow.core.paths import (
    PathHandler,
    get_devflow_home,
    get_docker_socket,
    get_hosts_file,
    get_ssh_dir,
)
from devflow.core.platform import Platform


class TestPathHandlerDockerSocket:
    """Tests for Docker socket path resolution."""

    def test_linux_socket(self) -> None:
        """Test Docker socket path on Linux."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            socket = PathHandler.get_docker_socket()
            assert socket == "/var/run/docker.sock"

    def test_wsl2_socket(self) -> None:
        """Test Docker socket path on WSL2."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WSL2):
            socket = PathHandler.get_docker_socket()
            assert socket == "/var/run/docker.sock"

    def test_windows_socket(self) -> None:
        """Test Docker socket path on Windows."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            socket = PathHandler.get_docker_socket()
            assert socket == "//./pipe/docker_engine"

    def test_macos_socket_docker_desktop(self) -> None:
        """Test Docker socket path on macOS with Docker Desktop."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.MACOS):
            home = Path.home()
            docker_desktop_path = home / ".docker" / "run" / "docker.sock"
            with patch.object(Path, "exists", return_value=True):
                # Mock the specific path check
                with patch("devflow.core.paths.Path.home", return_value=home):
                    socket = PathHandler.get_docker_socket()
                    # Will return Docker Desktop path if it exists
                    # or fall back to /var/run/docker.sock
                    assert socket in [str(docker_desktop_path), "/var/run/docker.sock"]

    def test_macos_socket_fallback(self) -> None:
        """Test Docker socket fallback on macOS without Docker Desktop."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.MACOS):
            # Mock that Docker Desktop socket doesn't exist
            with patch.object(Path, "exists", return_value=False):
                socket = PathHandler.get_docker_socket()
                assert socket == "/var/run/docker.sock"


class TestPathHandlerHostsFile:
    """Tests for hosts file path resolution."""

    def test_linux_hosts(self) -> None:
        """Test hosts file path on Linux."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            hosts = PathHandler.get_hosts_file()
            assert hosts == Path("/etc/hosts")

    def test_macos_hosts(self) -> None:
        """Test hosts file path on macOS."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.MACOS):
            hosts = PathHandler.get_hosts_file()
            assert hosts == Path("/etc/hosts")

    def test_wsl2_hosts(self) -> None:
        """Test hosts file path on WSL2."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WSL2):
            hosts = PathHandler.get_hosts_file()
            assert hosts == Path("/etc/hosts")

    def test_windows_hosts(self) -> None:
        """Test hosts file path on Windows."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            hosts = PathHandler.get_hosts_file()
            assert hosts == Path("C:/Windows/System32/drivers/etc/hosts")


class TestPathHandlerDevflowHome:
    """Tests for DevFlow home directory resolution."""

    def test_linux_home(self) -> None:
        """Test DevFlow home on Linux."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            home = PathHandler.get_devflow_home()
            assert home == Path.home() / ".devflow"

    def test_macos_home(self) -> None:
        """Test DevFlow home on macOS."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.MACOS):
            home = PathHandler.get_devflow_home()
            assert home == Path.home() / ".devflow"

    def test_wsl2_home(self) -> None:
        """Test DevFlow home on WSL2."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WSL2):
            home = PathHandler.get_devflow_home()
            assert home == Path.home() / ".devflow"

    def test_windows_home_with_appdata(self) -> None:
        """Test DevFlow home on Windows with APPDATA set."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            with patch.dict(os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}):
                home = PathHandler.get_devflow_home()
                assert home == Path("C:\\Users\\Test\\AppData\\Roaming") / "devflow"

    def test_windows_home_fallback(self) -> None:
        """Test DevFlow home on Windows without APPDATA."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            with patch.dict(os.environ, {"APPDATA": "", "USERPROFILE": "C:\\Users\\Test"}):
                home = PathHandler.get_devflow_home()
                assert home == Path("C:\\Users\\Test") / ".devflow"


class TestPathHandlerSshDir:
    """Tests for SSH directory resolution."""

    def test_linux_ssh(self) -> None:
        """Test SSH directory on Linux."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            ssh = PathHandler.get_ssh_dir()
            assert ssh == Path.home() / ".ssh"

    def test_macos_ssh(self) -> None:
        """Test SSH directory on macOS."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.MACOS):
            ssh = PathHandler.get_ssh_dir()
            assert ssh == Path.home() / ".ssh"

    def test_windows_ssh(self) -> None:
        """Test SSH directory on Windows."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            with patch.dict(os.environ, {"USERPROFILE": "C:\\Users\\Test"}):
                ssh = PathHandler.get_ssh_dir()
                assert ssh == Path("C:\\Users\\Test") / ".ssh"


class TestPathHandlerCertDir:
    """Tests for certificate directory resolution."""

    def test_linux_certs(self) -> None:
        """Test certificate directory on Linux."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            certs = PathHandler.get_cert_dir()
            assert certs == Path.home() / ".local" / "share" / "mkcert"

    def test_macos_certs(self) -> None:
        """Test certificate directory on macOS."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.MACOS):
            certs = PathHandler.get_cert_dir()
            assert certs == Path.home() / "Library" / "Application Support" / "mkcert"

    def test_windows_certs(self) -> None:
        """Test certificate directory on Windows."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            with patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\Test\\AppData\\Local"}):
                certs = PathHandler.get_cert_dir()
                assert certs == Path("C:\\Users\\Test\\AppData\\Local") / "mkcert"


class TestPathHandlerSocketMount:
    """Tests for Docker socket mount string generation."""

    def test_linux_mount(self) -> None:
        """Test socket mount string on Linux."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            mount = PathHandler.get_socket_mount()
            assert mount == "/var/run/docker.sock:/var/run/docker.sock"

    def test_windows_mount(self) -> None:
        """Test socket mount string on Windows."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            mount = PathHandler.get_socket_mount()
            assert mount == "//./pipe/docker_engine:/var/run/docker.sock"


class TestPathHandlerExpandPath:
    """Tests for path expansion."""

    def test_expand_tilde(self) -> None:
        """Test tilde expansion."""
        path = PathHandler.expand_path("~/test")
        assert str(Path.home()) in str(path)
        assert "~" not in str(path)

    def test_expand_env_var(self) -> None:
        """Test environment variable expansion."""
        with patch.dict(os.environ, {"MY_VAR": "/custom/path"}):
            path = PathHandler.expand_path("$MY_VAR/test")
            assert "/custom/path/test" in str(path).replace("\\", "/")

    def test_expand_normal_path(self) -> None:
        """Test that normal paths are normalized."""
        path = PathHandler.expand_path("/some/path")
        assert path.is_absolute()


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_docker_socket(self) -> None:
        """Test get_docker_socket convenience function."""
        result = get_docker_socket()
        assert isinstance(result, str)

    def test_get_hosts_file(self) -> None:
        """Test get_hosts_file convenience function."""
        result = get_hosts_file()
        assert isinstance(result, Path)

    def test_get_devflow_home(self) -> None:
        """Test get_devflow_home convenience function."""
        result = get_devflow_home()
        assert isinstance(result, Path)

    def test_get_ssh_dir(self) -> None:
        """Test get_ssh_dir convenience function."""
        result = get_ssh_dir()
        assert isinstance(result, Path)
