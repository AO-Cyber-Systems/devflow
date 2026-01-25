"""APT package manager installer for Debian/Ubuntu systems."""

from __future__ import annotations

from typing import Callable

from .base import InstallerBase, InstallProgress, InstallResult, PackageManager
from .platform import PlatformInfo, check_command_exists


class AptInstaller(InstallerBase):
    """Installer using APT package manager (Debian/Ubuntu)."""

    @property
    def package_manager(self) -> PackageManager:
        return PackageManager.APT

    async def is_available(self) -> bool:
        """Check if APT is available."""
        return check_command_exists("apt") or check_command_exists("apt-get")

    async def install(
        self,
        package: str,
        progress_callback: Callable[[InstallProgress], None] | None = None,
        use_sudo: bool = True,
    ) -> InstallResult:
        """Install a package using APT."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="APT is not available on this system",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Installing",
                    message=f"Installing {package} via APT...",
                    percent=10,
                )
            )

        # Build command
        cmd = []
        if use_sudo:
            cmd.append("sudo")
        cmd.extend(["apt-get", "install", "-y", package])

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
            # Check for common errors
            error_msg = stderr or stdout
            if "Unable to locate package" in error_msg:
                return InstallResult(
                    success=False,
                    message=f"Package {package} not found in APT repositories",
                    error_details="You may need to add a PPA or external repository",
                )
            elif "Permission denied" in error_msg or "are you root?" in error_msg:
                return InstallResult(
                    success=False,
                    message="Permission denied - sudo access required",
                    error_details=error_msg,
                )
            else:
                return InstallResult(
                    success=False,
                    message=f"Failed to install {package}",
                    error_details=error_msg,
                )

    async def uninstall(self, package: str, use_sudo: bool = True) -> InstallResult:
        """Uninstall a package using APT."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="APT is not available on this system",
            )

        cmd = []
        if use_sudo:
            cmd.append("sudo")
        cmd.extend(["apt-get", "remove", "-y", package])

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
        """Update a package using APT."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="APT is not available on this system",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Updating",
                    message=f"Updating {package}...",
                    percent=10,
                )
            )

        # First update package lists
        update_cmd = ["sudo", "apt-get", "update"] if use_sudo else ["apt-get", "update"]
        await self.run_command(update_cmd, stage="Updating lists", timeout=120)

        # Then upgrade the package
        cmd = []
        if use_sudo:
            cmd.append("sudo")
        cmd.extend(["apt-get", "install", "--only-upgrade", "-y", package])

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
        """Check if a package is installed via APT."""
        if not await self.is_available():
            return False

        success, stdout, _ = await self.run_command(
            ["dpkg", "-s", package],
            timeout=10,
        )

        if success and stdout:
            return "Status: install ok installed" in stdout

        return False

    async def get_installed_version(self, package: str) -> str | None:
        """Get the installed version of an APT package."""
        if not await self.is_available():
            return None

        success, stdout, _ = await self.run_command(
            ["dpkg-query", "-W", "-f=${Version}", package],
            timeout=10,
        )

        if success and stdout:
            return stdout.strip()

        return None

    async def update_package_lists(
        self,
        progress_callback: Callable[[InstallProgress], None] | None = None,
        use_sudo: bool = True,
    ) -> InstallResult:
        """Update APT package lists."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="APT is not available on this system",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Updating",
                    message="Updating package lists...",
                    percent=10,
                )
            )

        cmd = ["sudo", "apt-get", "update"] if use_sudo else ["apt-get", "update"]

        success, stdout, stderr = await self.run_command(
            cmd,
            progress_callback=progress_callback,
            stage="Updating",
            timeout=120,
        )

        if success:
            return InstallResult(
                success=True,
                message="Successfully updated package lists",
            )
        else:
            return InstallResult(
                success=False,
                message="Failed to update package lists",
                error_details=stderr or stdout,
            )

    async def add_repository(
        self,
        repo: str,
        progress_callback: Callable[[InstallProgress], None] | None = None,
        use_sudo: bool = True,
    ) -> InstallResult:
        """Add a PPA or repository to APT sources."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="APT is not available on this system",
            )

        # Check if add-apt-repository is available
        if not check_command_exists("add-apt-repository"):
            # Try to install software-properties-common
            install_result = await self.install("software-properties-common", progress_callback)
            if not install_result.success:
                return InstallResult(
                    success=False,
                    message="Could not install add-apt-repository",
                    error_details=install_result.error_details,
                )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Adding repository",
                    message=f"Adding {repo}...",
                    percent=10,
                )
            )

        cmd = []
        if use_sudo:
            cmd.append("sudo")
        cmd.extend(["add-apt-repository", "-y", repo])

        success, stdout, stderr = await self.run_command(
            cmd,
            progress_callback=progress_callback,
            stage="Adding repository",
            timeout=120,
        )

        if success:
            # Update package lists after adding repo
            await self.update_package_lists(progress_callback, use_sudo)
            return InstallResult(
                success=True,
                message=f"Successfully added repository {repo}",
            )
        else:
            return InstallResult(
                success=False,
                message=f"Failed to add repository {repo}",
                error_details=stderr or stdout,
            )
