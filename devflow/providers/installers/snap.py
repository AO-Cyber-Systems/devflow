"""Snap package manager installer for Linux systems."""

from __future__ import annotations

from typing import Callable

from .base import InstallerBase, InstallProgress, InstallResult, PackageManager
from .platform import PlatformInfo, check_command_exists


class SnapInstaller(InstallerBase):
    """Installer using Snap package manager."""

    @property
    def package_manager(self) -> PackageManager:
        return PackageManager.SNAP

    async def is_available(self) -> bool:
        """Check if Snap is available."""
        return check_command_exists("snap")

    async def install(
        self,
        package: str,
        progress_callback: Callable[[InstallProgress], None] | None = None,
        classic: bool = False,
        use_sudo: bool = True,
    ) -> InstallResult:
        """
        Install a package using Snap.

        Args:
            package: The snap package name
            classic: Whether to use --classic confinement
            use_sudo: Whether to use sudo (required for most snaps)
        """
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="Snap is not available on this system",
                error_details="Install snapd: sudo apt install snapd",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Installing",
                    message=f"Installing {package} via Snap...",
                    percent=10,
                )
            )

        # Build command
        cmd = []
        if use_sudo:
            cmd.append("sudo")
        cmd.extend(["snap", "install", package])

        if classic:
            cmd.append("--classic")

        success, stdout, stderr = await self.run_command(
            cmd,
            progress_callback=progress_callback,
            stage="Installing",
            timeout=600,
        )

        if success:
            version = await self.get_installed_version(package)
            return InstallResult(
                success=True,
                message=f"Successfully installed {package}",
                version=version,
            )
        else:
            error_msg = stderr or stdout

            # Check for common errors
            if "already installed" in error_msg.lower():
                return InstallResult(
                    success=True,
                    message=f"{package} is already installed",
                )
            elif "requires classic confinement" in error_msg.lower():
                # Retry with --classic
                return await self.install(package, progress_callback, classic=True, use_sudo=use_sudo)
            elif "snap not found" in error_msg.lower():
                return InstallResult(
                    success=False,
                    message=f"Snap package {package} not found",
                    error_details="Check available packages at https://snapcraft.io/store",
                )
            else:
                return InstallResult(
                    success=False,
                    message=f"Failed to install {package}",
                    error_details=error_msg,
                )

    async def uninstall(self, package: str, use_sudo: bool = True) -> InstallResult:
        """Uninstall a package using Snap."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="Snap is not available on this system",
            )

        cmd = []
        if use_sudo:
            cmd.append("sudo")
        cmd.extend(["snap", "remove", package])

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
        use_sudo: bool = True,
    ) -> InstallResult:
        """Update a package using Snap."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="Snap is not available on this system",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Updating",
                    message=f"Updating {package}...",
                    percent=10,
                )
            )

        cmd = []
        if use_sudo:
            cmd.append("sudo")
        cmd.extend(["snap", "refresh", package])

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
            error_msg = stderr or stdout
            if "no updates available" in error_msg.lower():
                return InstallResult(
                    success=True,
                    message=f"{package} is already at the latest version",
                )
            return InstallResult(
                success=False,
                message=f"Failed to update {package}",
                error_details=error_msg,
            )

    async def is_installed(self, package: str) -> bool:
        """Check if a package is installed via Snap."""
        if not await self.is_available():
            return False

        success, stdout, _ = await self.run_command(
            ["snap", "list", package],
            timeout=10,
        )

        return success and package in stdout

    async def get_installed_version(self, package: str) -> str | None:
        """Get the installed version of a Snap package."""
        if not await self.is_available():
            return None

        success, stdout, _ = await self.run_command(
            ["snap", "info", package],
            timeout=10,
        )

        if success and stdout:
            # Parse snap info output
            for line in stdout.split("\n"):
                if line.startswith("installed:"):
                    # Format: "installed: version (revision) size"
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]

        return None

    async def list_installed(self) -> list[dict[str, str]]:
        """List all installed Snap packages."""
        if not await self.is_available():
            return []

        success, stdout, _ = await self.run_command(
            ["snap", "list"],
            timeout=30,
        )

        if not success or not stdout:
            return []

        results = []
        lines = stdout.strip().split("\n")

        # Skip header line
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 3:
                results.append(
                    {
                        "name": parts[0],
                        "version": parts[1],
                        "revision": parts[2],
                    }
                )

        return results

    async def refresh_all(
        self,
        progress_callback: Callable[[InstallProgress], None] | None = None,
        use_sudo: bool = True,
    ) -> InstallResult:
        """Update all installed Snap packages."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="Snap is not available on this system",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Updating",
                    message="Updating all Snap packages...",
                    percent=10,
                )
            )

        cmd = []
        if use_sudo:
            cmd.append("sudo")
        cmd.extend(["snap", "refresh"])

        success, stdout, stderr = await self.run_command(
            cmd,
            progress_callback=progress_callback,
            stage="Updating",
            timeout=900,  # 15 minutes for all packages
        )

        if success:
            return InstallResult(
                success=True,
                message="Successfully updated all Snap packages",
            )
        else:
            return InstallResult(
                success=False,
                message="Failed to update Snap packages",
                error_details=stderr or stdout,
            )
