"""
Installers module for cross-platform tool installation.

This module provides a unified interface for installing development tools
across different platforms and package managers.
"""

from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from .base import (
    InstallerBase,
    InstallProgress,
    InstallResult,
    InstallStatus,
    ToolCategory,
    ToolDetector,
    ToolInfo,
    ToolStatus,
)
from .platform import (
    Architecture,
    LinuxDistro,
    OperatingSystem,
    PackageManager,
    PlatformInfo,
    check_command_exists,
    detect_platform,
    get_command_path,
    get_command_version,
    refresh_platform_info,
)
from .registry import (
    ALL_TOOLS,
    ESSENTIAL_TOOLS,
    TOOLS_BY_CATEGORY,
    get_mise_managed_tools,
    get_tool_by_id,
    get_tools_by_category,
)

# Import installers
from .apt import AptInstaller
from .brew import BrewInstaller
from .mise import MiseInstaller
from .snap import SnapInstaller
from .winget import WingetInstaller

__all__ = [
    # Base classes
    "InstallerBase",
    "InstallProgress",
    "InstallResult",
    "InstallStatus",
    "ToolCategory",
    "ToolDetector",
    "ToolInfo",
    "ToolStatus",
    # Platform detection
    "Architecture",
    "LinuxDistro",
    "OperatingSystem",
    "PackageManager",
    "PlatformInfo",
    "check_command_exists",
    "detect_platform",
    "get_command_path",
    "get_command_version",
    "refresh_platform_info",
    # Registry
    "ALL_TOOLS",
    "ESSENTIAL_TOOLS",
    "TOOLS_BY_CATEGORY",
    "get_mise_managed_tools",
    "get_tool_by_id",
    "get_tools_by_category",
    # Installers
    "AptInstaller",
    "BrewInstaller",
    "MiseInstaller",
    "SnapInstaller",
    "WingetInstaller",
    # Factory function
    "get_installer",
    "get_available_installers",
]


def get_installer(package_manager: PackageManager, platform_info: PlatformInfo | None = None) -> InstallerBase | None:
    """
    Get an installer instance for the specified package manager.

    Args:
        package_manager: The package manager to use
        platform_info: Optional platform info (will detect if not provided)

    Returns:
        An installer instance or None if not available
    """
    platform_info = platform_info or detect_platform()

    installer_map: dict[PackageManager, type[InstallerBase]] = {
        PackageManager.BREW: BrewInstaller,
        PackageManager.APT: AptInstaller,
        PackageManager.SNAP: SnapInstaller,
        PackageManager.WINGET: WingetInstaller,
        PackageManager.MISE: MiseInstaller,
    }

    installer_class = installer_map.get(package_manager)
    if installer_class:
        return installer_class(platform_info)

    return None


def get_available_installers(platform_info: PlatformInfo | None = None) -> list[InstallerBase]:
    """
    Get all available installers for the current platform.

    Args:
        platform_info: Optional platform info (will detect if not provided)

    Returns:
        List of available installer instances
    """
    platform_info = platform_info or detect_platform()

    installers = []
    for pm in platform_info.package_managers:
        installer = get_installer(pm, platform_info)
        if installer:
            installers.append(installer)

    return installers


async def install_tool(
    tool: ToolInfo,
    progress_callback: Callable[[InstallProgress], None] | None = None,
    platform_info: PlatformInfo | None = None,
    preferred_method: PackageManager | None = None,
) -> InstallResult:
    """
    Install a tool using the best available method.

    Args:
        tool: The tool to install
        progress_callback: Optional callback for progress updates
        platform_info: Optional platform info (will detect if not provided)
        preferred_method: Optional preferred package manager

    Returns:
        InstallResult indicating success or failure
    """
    platform_info = platform_info or detect_platform()
    detector = ToolDetector(platform_info)
    status = detector.detect_tool(tool)

    if status.status == InstallStatus.INSTALLED:
        return InstallResult(
            success=True,
            message=f"{tool.name} is already installed",
            version=status.version,
        )

    if not status.install_methods:
        return InstallResult(
            success=False,
            message=f"No installation method available for {tool.name}",
            error_details=f"Visit {tool.website} for manual installation",
        )

    # Select installation method
    method = preferred_method if preferred_method in status.install_methods else status.install_methods[0]

    installer = get_installer(method, platform_info)
    if not installer:
        return InstallResult(
            success=False,
            message=f"Could not create installer for {method.value}",
        )

    # Get the appropriate package name for this method
    package = _get_package_for_method(tool, method)
    if not package:
        return InstallResult(
            success=False,
            message=f"No package defined for {tool.name} via {method.value}",
        )

    # Special handling for certain installers
    if method == PackageManager.BREW and tool.brew_cask:
        brew_installer = installer  # type: ignore
        if hasattr(brew_installer, "install_cask"):
            return await brew_installer.install_cask(package, progress_callback)

    if method == PackageManager.SNAP and tool.snap_classic:
        snap_installer = installer  # type: ignore
        return await snap_installer.install(package, progress_callback, classic=True)

    return await installer.install(package, progress_callback)


def _get_package_for_method(tool: ToolInfo, method: PackageManager) -> str | None:
    """Get the package name for a specific installation method."""
    method_to_attr = {
        PackageManager.BREW: "brew_cask" if tool.brew_cask else "brew_package",
        PackageManager.APT: "apt_package",
        PackageManager.SNAP: "snap_package",
        PackageManager.WINGET: "winget_id",
        PackageManager.SCOOP: "scoop_package",
        PackageManager.MISE: "mise_package",
        PackageManager.NPM: "npm_package",
    }

    attr = method_to_attr.get(method)
    if attr:
        return getattr(tool, attr, None)

    return None
