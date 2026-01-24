"""Cross-platform tests for Docker provider."""

from unittest.mock import patch

import pytest

from devflow.core.platform import Platform
from devflow.providers.docker import DockerProvider


class TestDockerProviderSocketPath:
    """Tests for Docker socket path resolution across platforms."""

    def test_socket_path_on_linux(self) -> None:
        """Test Docker socket path on Linux."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            provider = DockerProvider()
            socket = provider.get_socket_path()
            assert socket == "/var/run/docker.sock"

    def test_socket_path_on_wsl2(self) -> None:
        """Test Docker socket path on WSL2."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WSL2):
            provider = DockerProvider()
            socket = provider.get_socket_path()
            assert socket == "/var/run/docker.sock"

    def test_socket_path_on_windows(self) -> None:
        """Test Docker socket path on Windows."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            provider = DockerProvider()
            socket = provider.get_socket_path()
            assert socket == "//./pipe/docker_engine"

    def test_socket_path_on_macos_fallback(self) -> None:
        """Test Docker socket path on macOS without Docker Desktop."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.MACOS):
            with patch("pathlib.Path.exists", return_value=False):
                provider = DockerProvider()
                socket = provider.get_socket_path()
                assert socket == "/var/run/docker.sock"


class TestDockerProviderSocketMount:
    """Tests for Docker socket mount string generation."""

    def test_socket_mount_on_linux(self) -> None:
        """Test Docker socket mount string on Linux."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            provider = DockerProvider()
            mount = provider.get_socket_mount()
            assert mount == "/var/run/docker.sock:/var/run/docker.sock"

    def test_socket_mount_on_wsl2(self) -> None:
        """Test Docker socket mount string on WSL2."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WSL2):
            provider = DockerProvider()
            mount = provider.get_socket_mount()
            assert mount == "/var/run/docker.sock:/var/run/docker.sock"

    def test_socket_mount_on_windows(self) -> None:
        """Test Docker socket mount string on Windows."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            provider = DockerProvider()
            mount = provider.get_socket_mount()
            assert mount == "//./pipe/docker_engine:/var/run/docker.sock"

    def test_socket_mount_container_target_is_always_unix(self) -> None:
        """Test that container target is always Unix socket path."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            provider = DockerProvider()
            mount = provider.get_socket_mount()
            # Container side should always be Unix-style
            assert mount.endswith(":/var/run/docker.sock")
