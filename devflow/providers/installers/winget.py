"""Windows Package Manager (winget) installer for Windows systems."""

from __future__ import annotations

from typing import Callable

from .base import InstallerBase, InstallProgress, InstallResult, PackageManager
from .platform import PlatformInfo, check_command_exists


class WingetInstaller(InstallerBase):
    """Installer using Windows Package Manager (winget)."""

    @property
    def package_manager(self) -> PackageManager:
        return PackageManager.WINGET

    async def is_available(self) -> bool:
        """Check if winget is available."""
        return check_command_exists("winget")

    async def install(
        self,
        package: str,
        progress_callback: Callable[[InstallProgress], None] | None = None,
        accept_agreements: bool = True,
    ) -> InstallResult:
        """
        Install a package using winget.

        Package should be the winget package ID (e.g., "Microsoft.VisualStudioCode").
        """
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="winget is not available",
                error_details="winget is included in Windows 10 (22H2+) and Windows 11",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Installing",
                    message=f"Installing {package} via winget...",
                    percent=10,
                )
            )

        # Build command
        cmd = ["winget", "install", "--id", package, "--exact"]

        if accept_agreements:
            cmd.extend(["--accept-source-agreements", "--accept-package-agreements"])

        # Add silent flag for non-interactive install
        cmd.append("--silent")

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
                requires_restart=self._check_requires_restart(stdout + stderr),
            )
        else:
            error_msg = stderr or stdout

            # Check for common error conditions
            if "already installed" in error_msg.lower():
                return InstallResult(
                    success=True,
                    message=f"{package} is already installed",
                )
            elif "No package found" in error_msg:
                return InstallResult(
                    success=False,
                    message=f"Package {package} not found in winget",
                    error_details="Check the package ID at https://winget.run/",
                )
            else:
                return InstallResult(
                    success=False,
                    message=f"Failed to install {package}",
                    error_details=error_msg,
                )

    async def uninstall(self, package: str) -> InstallResult:
        """Uninstall a package using winget."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="winget is not available",
            )

        success, stdout, stderr = await self.run_command(
            ["winget", "uninstall", "--id", package, "--exact", "--silent"],
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
        """Update a package using winget."""
        if not await self.is_available():
            return InstallResult(
                success=False,
                message="winget is not available",
            )

        if progress_callback:
            progress_callback(
                InstallProgress(
                    stage="Updating",
                    message=f"Updating {package}...",
                    percent=10,
                )
            )

        success, stdout, stderr = await self.run_command(
            [
                "winget",
                "upgrade",
                "--id",
                package,
                "--exact",
                "--silent",
                "--accept-source-agreements",
            ],
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
            if "No applicable upgrade found" in error_msg:
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
        """Check if a package is installed via winget."""
        if not await self.is_available():
            return False

        success, stdout, _ = await self.run_command(
            ["winget", "list", "--id", package, "--exact"],
            timeout=30,
        )

        # If package is found, it will be listed in output
        return success and package.lower() in stdout.lower()

    async def get_installed_version(self, package: str) -> str | None:
        """Get the installed version of a winget package."""
        if not await self.is_available():
            return None

        success, stdout, _ = await self.run_command(
            ["winget", "list", "--id", package, "--exact"],
            timeout=30,
        )

        if success and stdout:
            # Parse winget list output to extract version
            # Output format varies, but version is typically in a column
            lines = stdout.strip().split("\n")
            for line in lines:
                if package.lower() in line.lower():
                    # Version is usually the second or third column
                    parts = line.split()
                    for part in parts:
                        # Version typically contains digits and dots
                        if any(c.isdigit() for c in part) and "." in part:
                            return part.strip()

        return None

    async def search(self, query: str) -> list[dict[str, str]]:
        """Search for packages in winget."""
        if not await self.is_available():
            return []

        success, stdout, _ = await self.run_command(
            ["winget", "search", query, "--accept-source-agreements"],
            timeout=60,
        )

        if not success or not stdout:
            return []

        results = []
        lines = stdout.strip().split("\n")

        # Skip header lines
        data_started = False
        for line in lines:
            if "---" in line:
                data_started = True
                continue
            if not data_started:
                continue

            parts = line.split()
            if len(parts) >= 2:
                results.append(
                    {
                        "name": " ".join(parts[:-2]) if len(parts) > 2 else parts[0],
                        "id": parts[-2] if len(parts) > 2 else parts[-1],
                        "version": parts[-1] if len(parts) > 2 else "",
                    }
                )

        return results

    async def list_upgradable(self) -> list[dict[str, str]]:
        """List packages that have updates available."""
        if not await self.is_available():
            return []

        success, stdout, _ = await self.run_command(
            ["winget", "upgrade", "--accept-source-agreements"],
            timeout=60,
        )

        if not success or not stdout:
            return []

        results = []
        lines = stdout.strip().split("\n")

        # Skip header lines
        data_started = False
        for line in lines:
            if "---" in line:
                data_started = True
                continue
            if not data_started:
                continue
            if "upgrades available" in line.lower():
                break

            parts = line.split()
            if len(parts) >= 4:
                results.append(
                    {
                        "name": parts[0],
                        "id": parts[1],
                        "current_version": parts[2],
                        "available_version": parts[3],
                    }
                )

        return results

    def _check_requires_restart(self, output: str) -> bool:
        """Check if installation output indicates a restart is required."""
        restart_indicators = [
            "restart",
            "reboot",
            "log off",
            "sign out",
        ]
        output_lower = output.lower()
        return any(indicator in output_lower for indicator in restart_indicators)
