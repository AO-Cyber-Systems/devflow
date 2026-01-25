"""Homebrew package manager installer for macOS and Linux."""

from __future__ import annotations

from typing import Callable

from .base import InstallerBase, InstallProgress, InstallResult, PackageManager
from .platform import PlatformInfo, check_command_exists


class BrewInstaller(InstallerBase):
    """Installer using Homebrew package manager."""

    @property
    def package_manager(self) -> PackageManager:
        return PackageManager.BREW

    async def is_available(self) -> bool:
        """Check if Homebrew is installed."""
        return check_command_exists("brew")

    async def install(
        self,
        package: str,
        progress_callback: Callable[[InstallProgress], None] | None = None,
        is_cask: bool = False,
    ) -> InstallResult:
        """Install a package using Homebrew."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="Homebrew is not installed",
                error_details="Install Homebrew first: https://brew.sh/",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Installing",
                    message=f"Installing {package} via Homebrew...",
                    percent=10,
                )
            )

        # Build command
        cmd = ["brew", "install"]
        if is_cask:
            cmd.append("--cask")
        cmd.append(package)

        success, stdout, stderr = await self.run_command(
            cmd,
            progress_callback=progress_callback,
            stage="Installing",
            timeout=600,  # 10 minutes for large packages
        )

        if success:
            version = await self.get_installed_version(package)
            return InstallResult(
                success=True,
                message=f"Successfully installed {package}",
                version=version,
            )
        else:
            return InstallResult(
                success=False,
                message=f"Failed to install {package}",
                error_details=stderr or stdout,
            )

    async def install_cask(
        self,
        package: str,
        progress_callback: Callable[[InstallProgress], None] | None = None,
    ) -> InstallResult:
        """Install a cask (GUI application) using Homebrew."""
        return await self.install(package, progress_callback, is_cask=True)

    async def uninstall(self, package: str, is_cask: bool = False) -> InstallResult:
        """Uninstall a package using Homebrew."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="Homebrew is not installed",
            )

        cmd = ["brew", "uninstall"]
        if is_cask:
            cmd.append("--cask")
        cmd.append(package)

        success, stdout, stderr = await self.run_command(cmd, stage="Uninstalling")

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
        is_cask: bool = False,
    ) -> InstallResult:
        """Update a package using Homebrew."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="Homebrew is not installed",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Updating",
                    message=f"Updating {package}...",
                    percent=10,
                )
            )

        cmd = ["brew", "upgrade"]
        if is_cask:
            cmd.append("--cask")
        cmd.append(package)

        success, stdout, stderr = await self.run_command(
            cmd,
            progress_callback=progress_callback,
            stage="Updating",
            timeout=600,
        )

        if success:
            version = await self.get_installed_version(package)
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
        """Check if a package is installed via Homebrew."""
        if not await self.is_available():
            return False

        success, stdout, _ = await self.run_command(
            ["brew", "list", package],
            timeout=30,
        )
        return success

    async def get_installed_version(self, package: str) -> str | None:
        """Get the installed version of a Homebrew package."""
        if not await self.is_available():
            return None

        # Try formula first
        success, stdout, _ = await self.run_command(
            ["brew", "info", "--json=v2", package],
            timeout=30,
        )

        if success and stdout:
            try:
                import json

                data = json.loads(stdout)
                # Check formulae
                if data.get("formulae"):
                    formula = data["formulae"][0]
                    installed = formula.get("installed", [])
                    if installed:
                        return installed[0].get("version")
                # Check casks
                if data.get("casks"):
                    cask = data["casks"][0]
                    return cask.get("installed")
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        return None

    async def update_homebrew(
        self,
        progress_callback: Callable[[InstallProgress], None] | None = None,
    ) -> InstallResult:
        """Update Homebrew itself and all formulae."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="Homebrew is not installed",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Updating",
                    message="Updating Homebrew...",
                    percent=10,
                )
            )

        success, stdout, stderr = await self.run_command(
            ["brew", "update"],
            progress_callback=progress_callback,
            stage="Updating",
            timeout=300,
        )

        if success:
            return InstallResult(
                success=True,
                message="Successfully updated Homebrew",
            )
        else:
            return InstallResult(
                success=False,
                message="Failed to update Homebrew",
                error_details=stderr or stdout,
            )

    async def install_homebrew(
        self,
        progress_callback: Callable[[InstallProgress], None] | None = None,
    ) -> InstallResult:
        """Install Homebrew on macOS or Linux."""
        if await self.is_available():
            return InstallResult(
                success=True,
                message="Homebrew is already installed",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Installing",
                    message="Installing Homebrew...",
                    percent=10,
                )
            )

        # Homebrew installation requires running a shell script
        # We use /bin/bash explicitly with the install script
        install_script = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'

        # Note: This requires user interaction for sudo password
        # In a real implementation, we'd need to handle this differently
        return InstallResult(
            success=False,
            message="Homebrew installation requires manual setup",
            error_details=f"Please run: {install_script}",
        )
