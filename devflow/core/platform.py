"""Platform detection and abstraction for cross-platform compatibility.

This module provides platform detection to enable DevFlow to run on
Windows, Linux, macOS, and WSL2 with appropriate backend selection.
"""

import platform
from enum import Enum


class Platform(Enum):
    """Supported platforms for DevFlow."""

    LINUX = "linux"
    MACOS = "darwin"
    WINDOWS = "windows"
    WSL2 = "wsl2"


def detect_platform() -> Platform:
    """Detect the current platform.

    Returns:
        Platform enum value for the current operating system.

    Raises:
        RuntimeError: If the platform is not supported.
    """
    system = platform.system().lower()

    if system == "linux":
        # Check if running in WSL2 by examining the kernel release
        release = platform.uname().release.lower()
        if "microsoft" in release or "wsl" in release:
            return Platform.WSL2
        return Platform.LINUX
    elif system == "darwin":
        return Platform.MACOS
    elif system == "windows":
        return Platform.WINDOWS

    raise RuntimeError(f"Unsupported platform: {system}")


def is_wsl() -> bool:
    """Check if running inside WSL (1 or 2).

    Returns:
        True if running in WSL, False otherwise.
    """
    if platform.system().lower() != "linux":
        return False

    release = platform.uname().release.lower()
    return "microsoft" in release or "wsl" in release


def is_wsl2() -> bool:
    """Check if running inside WSL2 specifically.

    Returns:
        True if running in WSL2, False otherwise.
    """
    return detect_platform() == Platform.WSL2


def is_windows() -> bool:
    """Check if running on Windows (not WSL).

    Returns:
        True if running on native Windows, False otherwise.
    """
    return detect_platform() == Platform.WINDOWS


def is_macos() -> bool:
    """Check if running on macOS.

    Returns:
        True if running on macOS, False otherwise.
    """
    return detect_platform() == Platform.MACOS


def is_linux() -> bool:
    """Check if running on native Linux (not WSL).

    Returns:
        True if running on native Linux, False otherwise.
    """
    return detect_platform() == Platform.LINUX


def is_unix_like() -> bool:
    """Check if running on a Unix-like system (Linux, macOS, WSL).

    Returns:
        True if running on Linux, macOS, or WSL, False otherwise.
    """
    return detect_platform() in (Platform.LINUX, Platform.MACOS, Platform.WSL2)


# Module-level constant for the current platform
# Reason: Cached at module load time for efficiency since platform doesn't change
CURRENT_PLATFORM = detect_platform()
