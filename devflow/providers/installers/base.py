"""Base installer classes and interfaces."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from .platform import PackageManager, PlatformInfo, check_command_exists, detect_platform, get_command_version


class InstallStatus(str, Enum):
    """Status of a tool installation."""

    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    OUTDATED = "outdated"
    CHECKING = "checking"
    INSTALLING = "installing"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ToolCategory(str, Enum):
    """Categories of tools."""

    CODE_EDITOR = "code_editor"
    RUNTIME = "runtime"
    CONTAINER = "container"
    DATABASE = "database"
    SECRETS = "secrets"
    VERSION_CONTROL = "version_control"
    CLI_UTILITY = "cli_utility"
    SHELL = "shell"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class ToolInfo:
    """Information about a tool."""

    id: str
    name: str
    description: str
    category: ToolCategory
    website: str
    icon: str  # Lucide icon name

    # Detection
    binary: str | None = None  # Command to check (e.g., "code", "docker")
    version_flag: str = "--version"
    version_regex: str | None = None  # Regex to extract version from output

    # Installation availability by platform
    supports_macos: bool = True
    supports_linux: bool = True
    supports_windows: bool = True

    # Installation methods
    brew_package: str | None = None
    brew_cask: str | None = None
    apt_package: str | None = None
    snap_package: str | None = None
    snap_classic: bool = False
    winget_id: str | None = None
    scoop_package: str | None = None
    mise_package: str | None = None
    npm_package: str | None = None
    official_url: str | None = None

    # Flags
    requires_sudo: bool = False
    requires_restart: bool = False
    managed_by_mise: bool = False
    is_essential: bool = False

    # Dependencies
    depends_on: list[str] = field(default_factory=list)


@dataclass
class InstallResult:
    """Result of an installation attempt."""

    success: bool
    message: str
    version: str | None = None
    requires_restart: bool = False
    error_details: str | None = None


@dataclass
class InstallProgress:
    """Progress update during installation."""

    stage: str
    message: str
    percent: int  # 0-100
    is_complete: bool = False
    is_error: bool = False


@dataclass
class ToolStatus:
    """Current status of a tool."""

    tool_id: str
    status: InstallStatus
    version: str | None = None
    path: str | None = None
    can_install: bool = True
    can_update: bool = False
    install_methods: list[PackageManager] = field(default_factory=list)
    error_message: str | None = None


class InstallerBase(ABC):
    """Abstract base class for platform-specific installers."""

    def __init__(self, platform_info: PlatformInfo | None = None):
        self.platform = platform_info or detect_platform()

    @property
    @abstractmethod
    def package_manager(self) -> PackageManager:
        """Return the package manager this installer uses."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this installer is available on the current platform."""
        pass

    @abstractmethod
    async def install(
        self,
        package: str,
        progress_callback: Callable[[InstallProgress], None] | None = None,
    ) -> InstallResult:
        """Install a package."""
        pass

    @abstractmethod
    async def uninstall(self, package: str) -> InstallResult:
        """Uninstall a package."""
        pass

    @abstractmethod
    async def update(
        self,
        package: str,
        progress_callback: Callable[[InstallProgress], None] | None = None,
    ) -> InstallResult:
        """Update a package to the latest version."""
        pass

    @abstractmethod
    async def is_installed(self, package: str) -> bool:
        """Check if a package is installed."""
        pass

    @abstractmethod
    async def get_installed_version(self, package: str) -> str | None:
        """Get the installed version of a package."""
        pass

    async def run_command(
        self,
        cmd: list[str],
        progress_callback: Callable[[InstallProgress], None] | None = None,
        stage: str = "Running",
        timeout: int = 300,
    ) -> tuple[bool, str, str]:
        """
        Run a command asynchronously with progress updates.

        Uses subprocess with explicit arguments (no shell) for security.
        Returns (success, stdout, stderr).
        """
        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage=stage,
                    message=f"Running: {' '.join(cmd[:3])}...",
                    percent=10,
                )
            )

        try:
            # Reason: Using create_subprocess_exec (not shell) to prevent command injection
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            success = process.returncode == 0

            if progress_callback:
                progress_callback(
                    InstallProgress(
                        stage=stage,
                        message="Complete" if success else "Failed",
                        percent=100 if success else 0,
                        is_complete=success,
                        is_error=not success,
                    )
                )

            return success, stdout_str, stderr_str

        except asyncio.TimeoutError:
            if progress_callback:
                progress_callback(
                    InstallProgress(
                        stage=stage,
                        message="Command timed out",
                        percent=0,
                        is_error=True,
                    )
                )
            return False, "", "Command timed out"

        except Exception as e:
            if progress_callback:
                progress_callback(
                    InstallProgress(
                        stage=stage,
                        message=str(e),
                        percent=0,
                        is_error=True,
                    )
                )
            return False, "", str(e)


class ToolDetector:
    """Detects installed tools and their status."""

    def __init__(self, platform_info: PlatformInfo | None = None):
        self.platform = platform_info or detect_platform()
        self._cache: dict[str, ToolStatus] = {}

    def clear_cache(self) -> None:
        """Clear the detection cache."""
        self._cache.clear()

    def detect_tool(self, tool: ToolInfo) -> ToolStatus:
        """Detect the status of a single tool."""
        if tool.id in self._cache:
            return self._cache[tool.id]

        status = self._detect_tool_impl(tool)
        self._cache[tool.id] = status
        return status

    def _detect_tool_impl(self, tool: ToolInfo) -> ToolStatus:
        """Implementation of tool detection."""
        # Check platform support
        if not self._is_supported_on_platform(tool):
            return ToolStatus(
                tool_id=tool.id,
                status=InstallStatus.UNKNOWN,
                can_install=False,
                error_message=f"Not supported on {self.platform.os.value}",
            )

        # Check if binary exists
        if tool.binary:
            if check_command_exists(tool.binary):
                version = get_command_version(tool.binary, tool.version_flag)
                return ToolStatus(
                    tool_id=tool.id,
                    status=InstallStatus.INSTALLED,
                    version=version,
                    path=tool.binary,
                    can_install=True,
                    can_update=True,
                    install_methods=self._get_install_methods(tool),
                )
            else:
                return ToolStatus(
                    tool_id=tool.id,
                    status=InstallStatus.NOT_INSTALLED,
                    can_install=True,
                    install_methods=self._get_install_methods(tool),
                )

        # No binary to check - assume not installed
        return ToolStatus(
            tool_id=tool.id,
            status=InstallStatus.UNKNOWN,
            can_install=True,
            install_methods=self._get_install_methods(tool),
        )

    def _is_supported_on_platform(self, tool: ToolInfo) -> bool:
        """Check if tool is supported on current platform."""
        if self.platform.is_macos:
            return tool.supports_macos
        elif self.platform.is_linux:
            return tool.supports_linux
        elif self.platform.is_windows:
            return tool.supports_windows
        return False

    def _get_install_methods(self, tool: ToolInfo) -> list[PackageManager]:
        """Get available installation methods for a tool on this platform."""
        methods = []

        if self.platform.is_macos:
            if tool.brew_cask and self.platform.has_package_manager(PackageManager.BREW):
                methods.append(PackageManager.BREW)
            elif tool.brew_package and self.platform.has_package_manager(PackageManager.BREW):
                methods.append(PackageManager.BREW)

        if self.platform.is_linux:
            if tool.apt_package and self.platform.has_package_manager(PackageManager.APT):
                methods.append(PackageManager.APT)
            if tool.snap_package and self.platform.has_package_manager(PackageManager.SNAP):
                methods.append(PackageManager.SNAP)

        if self.platform.is_windows:
            if tool.winget_id and self.platform.has_package_manager(PackageManager.WINGET):
                methods.append(PackageManager.WINGET)
            if tool.scoop_package and self.platform.has_package_manager(PackageManager.SCOOP):
                methods.append(PackageManager.SCOOP)

        # Cross-platform methods
        if tool.mise_package and self.platform.has_package_manager(PackageManager.MISE):
            methods.append(PackageManager.MISE)
        if tool.npm_package and self.platform.has_package_manager(PackageManager.NPM):
            methods.append(PackageManager.NPM)

        return methods

    def detect_all(self, tools: list[ToolInfo]) -> dict[str, ToolStatus]:
        """Detect status of all provided tools."""
        results = {}
        for tool in tools:
            results[tool.id] = self.detect_tool(tool)
        return results
