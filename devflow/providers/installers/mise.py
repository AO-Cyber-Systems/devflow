"""Mise (polyglot version manager) installer and runtime manager."""

from __future__ import annotations

from typing import Callable

from .base import InstallerBase, InstallProgress, InstallResult, PackageManager
from .platform import PlatformInfo, check_command_exists, get_command_version


class MiseInstaller(InstallerBase):
    """Installer using Mise for language runtimes and tools."""

    @property
    def package_manager(self) -> PackageManager:
        return PackageManager.MISE

    async def is_available(self) -> bool:
        """Check if Mise is installed."""
        return check_command_exists("mise")

    async def get_mise_version(self) -> str | None:
        """Get the installed Mise version."""
        return get_command_version("mise")

    async def install(
        self,
        package: str,
        progress_callback: Callable[[InstallProgress], None] | None = None,
        version: str | None = None,
    ) -> InstallResult:
        """
        Install a runtime/tool using Mise.

        Package format: "node", "python", "node@22", "npm:prettier"
        """
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="Mise is not installed",
                error_details="Install Mise first: curl https://mise.run | sh",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Installing",
                    message=f"Installing {package} via Mise...",
                    percent=10,
                )
            )

        # Build package spec with version if provided
        package_spec = f"{package}@{version}" if version and "@" not in package else package

        # Use mise use to install and activate
        success, stdout, stderr = await self.run_command(
            ["mise", "use", "--global", package_spec],
            progress_callback=progress_callback,
            stage="Installing",
            timeout=600,
        )

        if success:
            installed_version = await self.get_installed_version(package.split("@")[0])
            return InstallResult(
                success=True,
                message=f"Successfully installed {package}",
                version=installed_version,
            )
        else:
            return InstallResult(
                success=False,
                message=f"Failed to install {package}",
                error_details=stderr or stdout,
            )

    async def uninstall(self, package: str) -> InstallResult:
        """Uninstall a runtime/tool using Mise."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="Mise is not installed",
            )

        # Get the tool name without version
        tool_name = package.split("@")[0]

        success, stdout, stderr = await self.run_command(
            ["mise", "uninstall", tool_name],
            stage="Uninstalling",
        )

        if success:
            return InstallResult(
                success=True,
                message=f"Successfully uninstalled {package}",
            )
        else:
            return InstallResult(
                success=False,
                message=f"Failed to uninstall {package}",
                error_details=stderr or stdout,
            )

    async def update(
        self,
        package: str,
        progress_callback: Callable[[InstallProgress], None] | None = None,
    ) -> InstallResult:
        """Update a runtime/tool to latest version using Mise."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="Mise is not installed",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Updating",
                    message=f"Updating {package}...",
                    percent=10,
                )
            )

        # Get the tool name without version
        tool_name = package.split("@")[0]

        # Use mise upgrade to update to latest
        success, stdout, stderr = await self.run_command(
            ["mise", "upgrade", tool_name],
            progress_callback=progress_callback,
            stage="Updating",
            timeout=600,
        )

        if success:
            version = await self.get_installed_version(tool_name)
            return InstallResult(
                success=True,
                message=f"Successfully updated {package}",
                version=version,
            )
        else:
            return InstallResult(
                success=False,
                message=f"Failed to update {package}",
                error_details=stderr or stdout,
            )

    async def is_installed(self, package: str) -> bool:
        """Check if a runtime/tool is installed via Mise."""
        if not await self.is_available():
            return False

        # Get the tool name without version
        tool_name = package.split("@")[0]

        success, stdout, _ = await self.run_command(
            ["mise", "list", tool_name],
            timeout=10,
        )

        # Check if there's any installed version
        return success and tool_name in stdout and "missing" not in stdout.lower()

    async def get_installed_version(self, package: str) -> str | None:
        """Get the currently active version of a tool."""
        if not await self.is_available():
            return None

        # Get the tool name without version
        tool_name = package.split("@")[0]

        success, stdout, _ = await self.run_command(
            ["mise", "current", tool_name],
            timeout=10,
        )

        if success and stdout:
            # Output format is typically: "tool version" or just "version"
            parts = stdout.strip().split()
            if len(parts) >= 1:
                # Return the version part
                version = parts[-1] if len(parts) > 1 else parts[0]
                if version and version != "missing":
                    return version

        return None

    async def list_installed(self) -> dict[str, str]:
        """List all installed tools and their versions."""
        if not await self.is_available():
            return {}

        success, stdout, _ = await self.run_command(
            ["mise", "list", "--json"],
            timeout=30,
        )

        if success and stdout:
            try:
                import json

                data = json.loads(stdout)
                result = {}
                for tool, versions in data.items():
                    if versions:
                        # Get the active/latest version
                        result[tool] = versions[0].get("version", "unknown")
                return result
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        return {}

    async def install_mise(
        self,
        progress_callback: Callable[[InstallProgress], None] | None = None,
    ) -> InstallResult:
        """
        Install Mise itself.

        This method provides installation instructions since Mise installation
        varies by platform and may require shell configuration.
        """
        if await self.is_available():
            version = await self.get_mise_version()
            return InstallResult(
                success=True,
                message=f"Mise is already installed (version: {version})",
                version=version,
            )

        # Try to install via curl
        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Installing",
                    message="Attempting to install Mise...",
                    percent=10,
                )
            )

        # Check platform for appropriate installation method
        if self.platform.is_macos and self.platform.has_package_manager(PackageManager.BREW):
            # Use Homebrew on macOS
            from .brew import BrewInstaller

            brew = BrewInstaller(self.platform)
            result = await brew.install("mise", progress_callback)
            if result.success:
                return InstallResult(
                    success=True,
                    message="Successfully installed Mise via Homebrew",
                    version=await self.get_mise_version(),
                )

        if self.platform.is_windows:
            # Use winget on Windows
            return InstallResult(
                success=False,
                message="Please install Mise manually on Windows",
                error_details="Run: winget install jdx.mise",
            )

        # For Linux/macOS without Homebrew, use curl installer
        # Note: This requires shell interaction, so we provide instructions
        return InstallResult(
            success=False,
            message="Mise installation requires shell configuration",
            error_details='Run: curl https://mise.run | sh\nThen add to your shell config: eval "$(mise activate bash)"',
        )

    async def trust_config(self, config_path: str | None = None) -> InstallResult:
        """Trust a mise configuration file."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="Mise is not installed",
            )

        cmd = ["mise", "trust"]
        if config_path:
            cmd.append(config_path)

        success, stdout, stderr = await self.run_command(cmd, timeout=10)

        if success:
            return InstallResult(
                success=True,
                message="Configuration trusted",
            )
        else:
            return InstallResult(
                success=False,
                message="Failed to trust configuration",
                error_details=stderr or stdout,
            )

    async def activate_shell(self, shell: str = "bash") -> str:
        """Get the shell activation command for Mise."""
        return f'eval "$(mise activate {shell})"'

    async def get_available_versions(self, tool: str) -> list[str]:
        """Get available versions for a tool."""
        if not await self.is_available():
            return []

        success, stdout, _ = await self.run_command(
            ["mise", "ls-remote", tool],
            timeout=60,
        )

        if success and stdout:
            versions = [v.strip() for v in stdout.strip().split("\n") if v.strip()]
            # Return most recent versions first (last 20)
            return list(reversed(versions[-20:]))

        return []
