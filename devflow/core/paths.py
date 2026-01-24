"""Cross-platform path handling for DevFlow.

This module provides platform-aware path resolution for Docker sockets,
configuration directories, hosts files, and other platform-specific paths.
"""

import os
from pathlib import Path

from .platform import CURRENT_PLATFORM, Platform


class PathHandler:
    """Platform-aware path handler for DevFlow.

    Provides static methods to resolve platform-specific paths for:
    - Docker socket
    - Hosts file
    - DevFlow home directory
    - SSH directory
    - Certificate directories
    """

    @staticmethod
    def get_docker_socket() -> str:
        """Get Docker socket path for current platform.

        Returns:
            Path to the Docker socket.

        Note:
            On macOS, tries Docker Desktop socket first, then falls back to standard path.
            On Windows, returns the named pipe path.
        """
        if CURRENT_PLATFORM == Platform.MACOS:
            # Try Docker Desktop socket first (newer Docker Desktop versions)
            home = Path.home()
            docker_desktop = home / ".docker" / "run" / "docker.sock"
            if docker_desktop.exists():
                return str(docker_desktop)
            # Fall back to standard path (older Docker Desktop or Colima)
            return "/var/run/docker.sock"

        elif CURRENT_PLATFORM in (Platform.LINUX, Platform.WSL2):
            return "/var/run/docker.sock"

        elif CURRENT_PLATFORM == Platform.WINDOWS:
            # Windows named pipe for Docker
            return "//./pipe/docker_engine"

        # Default fallback
        return "/var/run/docker.sock"

    @staticmethod
    def get_hosts_file() -> Path:
        """Get hosts file path for current platform.

        Returns:
            Path to the system hosts file.
        """
        if CURRENT_PLATFORM == Platform.WINDOWS:
            return Path("C:/Windows/System32/drivers/etc/hosts")
        return Path("/etc/hosts")

    @staticmethod
    def get_devflow_home() -> Path:
        """Get DevFlow home directory for current platform.

        Returns:
            Path to the DevFlow configuration/data directory.
        """
        if CURRENT_PLATFORM == Platform.WINDOWS:
            # Use APPDATA on Windows (typically C:\Users\<user>\AppData\Roaming)
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                return Path(appdata) / "devflow"
            # Fallback to user profile
            return Path(os.environ.get("USERPROFILE", "")) / ".devflow"

        # Unix-like systems use ~/.devflow
        return Path.home() / ".devflow"

    @staticmethod
    def get_ssh_dir() -> Path:
        """Get SSH directory for current platform.

        Returns:
            Path to the SSH configuration directory.
        """
        if CURRENT_PLATFORM == Platform.WINDOWS:
            user_profile = os.environ.get("USERPROFILE", "")
            if user_profile:
                return Path(user_profile) / ".ssh"

        return Path.home() / ".ssh"

    @staticmethod
    def get_cert_dir() -> Path:
        """Get default certificate directory for current platform.

        Returns:
            Path to the mkcert/certificate directory.
        """
        if CURRENT_PLATFORM == Platform.WINDOWS:
            appdata = os.environ.get("LOCALAPPDATA", "")
            if appdata:
                return Path(appdata) / "mkcert"
            return Path(os.environ.get("USERPROFILE", "")) / ".local" / "share" / "mkcert"

        elif CURRENT_PLATFORM == Platform.MACOS:
            return Path.home() / "Library" / "Application Support" / "mkcert"

        # Linux and WSL2
        return Path.home() / ".local" / "share" / "mkcert"

    @staticmethod
    def get_docker_config_dir() -> Path:
        """Get Docker configuration directory for current platform.

        Returns:
            Path to the Docker configuration directory.
        """
        if CURRENT_PLATFORM == Platform.WINDOWS:
            user_profile = os.environ.get("USERPROFILE", "")
            if user_profile:
                return Path(user_profile) / ".docker"

        return Path.home() / ".docker"

    @staticmethod
    def get_socket_mount() -> str:
        """Get Docker socket mount string for compose/swarm configurations.

        Returns:
            Mount string in format 'source:target' for Docker socket.
        """
        socket = PathHandler.get_docker_socket()

        if CURRENT_PLATFORM == Platform.WINDOWS:
            # Windows named pipe mounting
            return f"{socket}:/var/run/docker.sock"

        return f"{socket}:/var/run/docker.sock"

    @staticmethod
    def expand_path(path: str | Path) -> Path:
        """Expand a path with platform-appropriate handling.

        Handles:
        - ~ expansion
        - Environment variable expansion
        - Path normalization

        Args:
            path: Path string or Path object to expand.

        Returns:
            Expanded and normalized Path object.
        """
        path_str = str(path)

        # Expand ~ to home directory
        if path_str.startswith("~"):
            path_str = str(Path.home()) + path_str[1:]

        # Expand environment variables
        path_str = os.path.expandvars(path_str)

        return Path(path_str).resolve()


# Convenience functions for direct access
def get_docker_socket() -> str:
    """Get Docker socket path for current platform."""
    return PathHandler.get_docker_socket()


def get_hosts_file() -> Path:
    """Get hosts file path for current platform."""
    return PathHandler.get_hosts_file()


def get_devflow_home() -> Path:
    """Get DevFlow home directory for current platform."""
    return PathHandler.get_devflow_home()


def get_ssh_dir() -> Path:
    """Get SSH directory for current platform."""
    return PathHandler.get_ssh_dir()
