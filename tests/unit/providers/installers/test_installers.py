"""Tests for individual installer implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from devflow.providers.installers.apt import AptInstaller
from devflow.providers.installers.base import InstallProgress, InstallResult
from devflow.providers.installers.brew import BrewInstaller
from devflow.providers.installers.mise import MiseInstaller
from devflow.providers.installers.platform import (
    Architecture,
    LinuxDistro,
    OperatingSystem,
    PackageManager,
    PlatformInfo,
)
from devflow.providers.installers.snap import SnapInstaller
from devflow.providers.installers.winget import WingetInstaller


@pytest.fixture
def linux_platform() -> PlatformInfo:
    """Create a Linux platform info for testing."""
    return PlatformInfo(
        os=OperatingSystem.LINUX,
        os_version="5.15.0",
        distro=LinuxDistro.UBUNTU,
        distro_version="22.04",
        arch=Architecture.X86_64,
        is_wsl=False,
        package_managers=[PackageManager.APT, PackageManager.SNAP, PackageManager.MISE],
    )


@pytest.fixture
def macos_platform() -> PlatformInfo:
    """Create a macOS platform info for testing."""
    return PlatformInfo(
        os=OperatingSystem.MACOS,
        os_version="14.0",
        distro=None,
        distro_version=None,
        arch=Architecture.ARM64,
        is_wsl=False,
        package_managers=[PackageManager.BREW, PackageManager.MISE],
    )


@pytest.fixture
def windows_platform() -> PlatformInfo:
    """Create a Windows platform info for testing."""
    return PlatformInfo(
        os=OperatingSystem.WINDOWS,
        os_version="10",
        distro=None,
        distro_version=None,
        arch=Architecture.X86_64,
        is_wsl=False,
        package_managers=[PackageManager.WINGET, PackageManager.SCOOP],
    )


class TestBrewInstaller:
    """Tests for BrewInstaller."""

    def test_package_manager(self, macos_platform: PlatformInfo) -> None:
        """Test package manager property."""
        installer = BrewInstaller(macos_platform)
        assert installer.package_manager == PackageManager.BREW

    @pytest.mark.asyncio
    async def test_is_available_when_installed(self, macos_platform: PlatformInfo) -> None:
        """Test availability when brew is installed."""
        installer = BrewInstaller(macos_platform)
        with patch("shutil.which", return_value="/opt/homebrew/bin/brew"):
            assert await installer.is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_when_not_installed(self, macos_platform: PlatformInfo) -> None:
        """Test availability when brew is not installed."""
        installer = BrewInstaller(macos_platform)
        with patch("shutil.which", return_value=None):
            assert await installer.is_available() is False

    @pytest.mark.asyncio
    async def test_is_installed_true(self, macos_platform: PlatformInfo) -> None:
        """Test checking if a package is installed."""
        installer = BrewInstaller(macos_platform)
        installer.run_command = AsyncMock(return_value=(True, "", ""))
        assert await installer.is_installed("git") is True

    @pytest.mark.asyncio
    async def test_is_installed_false(self, macos_platform: PlatformInfo) -> None:
        """Test checking if a package is not installed."""
        installer = BrewInstaller(macos_platform)
        installer.run_command = AsyncMock(return_value=(False, "", "No such package"))
        assert await installer.is_installed("nonexistent") is False


class TestAptInstaller:
    """Tests for AptInstaller."""

    def test_package_manager(self, linux_platform: PlatformInfo) -> None:
        """Test package manager property."""
        installer = AptInstaller(linux_platform)
        assert installer.package_manager == PackageManager.APT

    @pytest.mark.asyncio
    async def test_is_available_when_apt_exists(self, linux_platform: PlatformInfo) -> None:
        """Test availability when apt is installed."""
        installer = AptInstaller(linux_platform)
        with patch("devflow.providers.installers.apt.check_command_exists", return_value=True):
            assert await installer.is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_when_apt_not_exists(self, linux_platform: PlatformInfo) -> None:
        """Test availability when apt is not installed."""
        installer = AptInstaller(linux_platform)
        with patch("devflow.providers.installers.apt.check_command_exists", return_value=False):
            assert await installer.is_available() is False

    @pytest.mark.asyncio
    async def test_is_installed_true(self, linux_platform: PlatformInfo) -> None:
        """Test checking if a package is installed."""
        installer = AptInstaller(linux_platform)
        with patch("devflow.providers.installers.apt.check_command_exists", return_value=True):
            installer.run_command = AsyncMock(return_value=(True, "Status: install ok installed", ""))
            assert await installer.is_installed("git") is True

    @pytest.mark.asyncio
    async def test_is_installed_false(self, linux_platform: PlatformInfo) -> None:
        """Test checking if a package is not installed."""
        installer = AptInstaller(linux_platform)
        with patch("devflow.providers.installers.apt.check_command_exists", return_value=True):
            installer.run_command = AsyncMock(return_value=(False, "", ""))
            assert await installer.is_installed("nonexistent") is False


class TestSnapInstaller:
    """Tests for SnapInstaller."""

    def test_package_manager(self, linux_platform: PlatformInfo) -> None:
        """Test package manager property."""
        installer = SnapInstaller(linux_platform)
        assert installer.package_manager == PackageManager.SNAP

    @pytest.mark.asyncio
    async def test_is_available_when_snap_exists(self, linux_platform: PlatformInfo) -> None:
        """Test availability when snap is installed."""
        installer = SnapInstaller(linux_platform)
        with patch("devflow.providers.installers.snap.check_command_exists", return_value=True):
            assert await installer.is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_when_snap_not_exists(self, linux_platform: PlatformInfo) -> None:
        """Test availability when snap is not installed."""
        installer = SnapInstaller(linux_platform)
        with patch("devflow.providers.installers.snap.check_command_exists", return_value=False):
            assert await installer.is_available() is False

    @pytest.mark.asyncio
    async def test_is_installed(self, linux_platform: PlatformInfo) -> None:
        """Test checking if a snap is installed."""
        installer = SnapInstaller(linux_platform)
        with patch("devflow.providers.installers.snap.check_command_exists", return_value=True):
            installer.run_command = AsyncMock(return_value=(True, "code 1.85.0", ""))
            assert await installer.is_installed("code") is True


class TestWingetInstaller:
    """Tests for WingetInstaller."""

    def test_package_manager(self, windows_platform: PlatformInfo) -> None:
        """Test package manager property."""
        installer = WingetInstaller(windows_platform)
        assert installer.package_manager == PackageManager.WINGET

    @pytest.mark.asyncio
    async def test_is_available_on_windows(self, windows_platform: PlatformInfo) -> None:
        """Test availability on Windows with winget."""
        installer = WingetInstaller(windows_platform)
        with patch("shutil.which", return_value="C:\\Program Files\\winget.exe"):
            assert await installer.is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_on_linux(self, linux_platform: PlatformInfo) -> None:
        """Test availability on Linux (should be False)."""
        installer = WingetInstaller(linux_platform)
        assert await installer.is_available() is False


class TestMiseInstaller:
    """Tests for MiseInstaller."""

    def test_package_manager(self, linux_platform: PlatformInfo) -> None:
        """Test package manager property."""
        installer = MiseInstaller(linux_platform)
        assert installer.package_manager == PackageManager.MISE

    @pytest.mark.asyncio
    async def test_is_available_when_installed(self, linux_platform: PlatformInfo) -> None:
        """Test availability when mise is installed."""
        installer = MiseInstaller(linux_platform)
        with patch("devflow.providers.installers.mise.check_command_exists", return_value=True):
            assert await installer.is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_when_not_installed(self, linux_platform: PlatformInfo) -> None:
        """Test availability when mise is not installed."""
        installer = MiseInstaller(linux_platform)
        with patch("devflow.providers.installers.mise.check_command_exists", return_value=False):
            assert await installer.is_available() is False

    @pytest.mark.asyncio
    async def test_get_mise_version(self, linux_platform: PlatformInfo) -> None:
        """Test getting mise version."""
        installer = MiseInstaller(linux_platform)
        with patch("devflow.providers.installers.mise.get_command_version", return_value="2024.1.0 linux-x64"):
            version = await installer.get_mise_version()
            assert version == "2024.1.0 linux-x64"

    @pytest.mark.asyncio
    async def test_is_installed(self, linux_platform: PlatformInfo) -> None:
        """Test checking if a tool is installed via mise."""
        installer = MiseInstaller(linux_platform)
        with patch("devflow.providers.installers.mise.check_command_exists", return_value=True):
            # mise list node returns the tool name and version
            installer.run_command = AsyncMock(return_value=(True, "node 20.10.0", ""))
            assert await installer.is_installed("node") is True

    @pytest.mark.asyncio
    async def test_list_installed(self, linux_platform: PlatformInfo) -> None:
        """Test listing installed tools."""
        import json

        installer = MiseInstaller(linux_platform)
        # Mise list --json returns a dict with tool names as keys
        mise_json_output = json.dumps({
            "node": [{"version": "20.10.0"}],
            "python": [{"version": "3.12.1"}],
        })
        with patch("devflow.providers.installers.mise.check_command_exists", return_value=True):
            installer.run_command = AsyncMock(return_value=(True, mise_json_output, ""))

            tools = await installer.list_installed()
            assert len(tools) == 2
            assert tools["node"] == "20.10.0"
            assert tools["python"] == "3.12.1"


class TestInstallProgress:
    """Tests for InstallProgress dataclass."""

    def test_creation(self) -> None:
        """Test creating an InstallProgress instance."""
        progress = InstallProgress(
            stage="Installing",
            message="Installing git...",
            percent=50,
        )
        assert progress.stage == "Installing"
        assert progress.message == "Installing git..."
        assert progress.percent == 50
        assert progress.is_complete is False
        assert progress.is_error is False

    def test_completion(self) -> None:
        """Test a completed progress."""
        progress = InstallProgress(
            stage="Complete",
            message="Installation complete",
            percent=100,
            is_complete=True,
        )
        assert progress.is_complete is True
        assert progress.percent == 100

    def test_error(self) -> None:
        """Test an error progress."""
        progress = InstallProgress(
            stage="Failed",
            message="Installation failed",
            percent=0,
            is_error=True,
        )
        assert progress.is_error is True


class TestInstallResult:
    """Tests for InstallResult dataclass."""

    def test_success(self) -> None:
        """Test a successful install result."""
        result = InstallResult(
            success=True,
            message="Installed git 2.40.0",
            version="2.40.0",
        )
        assert result.success is True
        assert result.message == "Installed git 2.40.0"
        assert result.version == "2.40.0"
        assert result.requires_restart is False
        assert result.error_details is None

    def test_failure(self) -> None:
        """Test a failed install result."""
        result = InstallResult(
            success=False,
            message="Failed to install",
            error_details="Package not found",
        )
        assert result.success is False
        assert result.error_details == "Package not found"
