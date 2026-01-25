"""Tests for setup handler."""

from unittest.mock import MagicMock, patch

import pytest

from bridge.handlers.setup import SetupHandler
from devflow.providers.installers.base import InstallStatus, ToolCategory
from devflow.providers.installers.platform import (
    Architecture,
    LinuxDistro,
    OperatingSystem,
    PackageManager,
    PlatformInfo,
)


@pytest.fixture
def mock_platform_info() -> PlatformInfo:
    """Create a mock platform info for testing."""
    return PlatformInfo(
        os=OperatingSystem.LINUX,
        os_version="5.15.0",
        distro=LinuxDistro.UBUNTU,
        distro_version="22.04",
        arch=Architecture.X86_64,
        is_wsl=True,
        package_managers=[PackageManager.APT, PackageManager.SNAP, PackageManager.MISE],
    )


@pytest.fixture
def setup_handler(mock_platform_info: PlatformInfo) -> SetupHandler:
    """Create a SetupHandler with mocked platform info."""
    handler = SetupHandler()
    handler._platform_info = mock_platform_info
    return handler


class TestSetupHandlerPlatformInfo:
    """Tests for platform info methods."""

    def test_get_platform_info(self, setup_handler: SetupHandler) -> None:
        """Test getting platform info."""
        info = setup_handler.get_platform_info()

        assert info["os"] == "linux"
        assert info["distro"] == "ubuntu"
        assert info["architecture"] == "x86_64"
        assert info["is_wsl"] is True
        assert info["is_linux"] is True
        assert info["is_macos"] is False
        assert info["is_windows"] is False
        assert "apt" in info["package_managers"]
        assert "snap" in info["package_managers"]

    def test_refresh_platform_info(self) -> None:
        """Test refreshing platform info clears cache."""
        handler = SetupHandler()
        # Set initial value
        handler._platform_info = PlatformInfo(
            os=OperatingSystem.LINUX,
            os_version="5.15",
            distro=LinuxDistro.UBUNTU,
            distro_version="22.04",
            arch=Architecture.X86_64,
            is_wsl=False,
            package_managers=[PackageManager.APT],
        )

        with patch("bridge.handlers.setup.detect_platform") as mock_detect:
            mock_detect.return_value = PlatformInfo(
                os=OperatingSystem.MACOS,
                os_version="14.0",
                distro=None,
                distro_version=None,
                arch=Architecture.ARM64,
                is_wsl=False,
                package_managers=[PackageManager.BREW],
            )

            result = handler.refresh_platform_info()
            assert result["os"] == "macos"


class TestSetupHandlerCategories:
    """Tests for category methods."""

    def test_get_categories(self, setup_handler: SetupHandler) -> None:
        """Test getting all categories."""
        categories = setup_handler.get_categories()

        assert len(categories) > 0
        assert "code_editor" in categories
        assert "runtime" in categories
        assert "container" in categories

        # Check category structure
        for cat_id, cat_info in categories.items():
            assert "name" in cat_info
            assert "tool_count" in cat_info
            assert "tool_ids" in cat_info
            assert cat_info["tool_count"] == len(cat_info["tool_ids"])


class TestSetupHandlerTools:
    """Tests for tool-related methods."""

    def test_get_all_tools(self, setup_handler: SetupHandler) -> None:
        """Test getting all tools."""
        tools = setup_handler.get_all_tools()

        assert len(tools) > 0
        for tool in tools:
            assert "id" in tool
            assert "name" in tool
            assert "description" in tool
            assert "category" in tool
            assert "command" in tool

    def test_get_essential_tools(self, setup_handler: SetupHandler) -> None:
        """Test getting essential tools."""
        tools = setup_handler.get_essential_tools()

        assert len(tools) > 0
        for tool in tools:
            assert tool["essential"] is True

    def test_get_tools_by_category(self, setup_handler: SetupHandler) -> None:
        """Test getting tools by category."""
        tools = setup_handler.get_tools_by_category("code_editor")

        assert len(tools) > 0
        for tool in tools:
            assert tool["category"] == "code_editor"

    def test_get_tools_by_invalid_category(self, setup_handler: SetupHandler) -> None:
        """Test getting tools by invalid category returns empty list."""
        tools = setup_handler.get_tools_by_category("invalid_category")
        assert tools == []

    def test_get_mise_managed_tools(self, setup_handler: SetupHandler) -> None:
        """Test getting Mise-managed tools."""
        tools = setup_handler.get_mise_managed_tools()

        assert len(tools) > 0
        for tool in tools:
            assert tool["mise_managed"] is True

    def test_get_tool(self, setup_handler: SetupHandler) -> None:
        """Test getting a specific tool."""
        tool = setup_handler.get_tool("git")

        assert tool is not None
        assert tool["id"] == "git"
        assert tool["name"] == "Git"
        assert tool["category"] == "version_control"

    def test_get_tool_not_found(self, setup_handler: SetupHandler) -> None:
        """Test getting a non-existent tool."""
        tool = setup_handler.get_tool("nonexistent")
        assert tool is None


class TestSetupHandlerDetection:
    """Tests for tool detection methods."""

    def test_detect_tool(self, setup_handler: SetupHandler) -> None:
        """Test detecting a single tool."""
        with patch("shutil.which", return_value="/usr/bin/git"):
            result = setup_handler.detect_tool("git")

            assert result["tool_id"] == "git"
            assert result["name"] == "Git"
            assert "status" in result
            assert "install_methods" in result

    def test_detect_tool_not_found(self, setup_handler: SetupHandler) -> None:
        """Test detecting a non-existent tool."""
        result = setup_handler.detect_tool("nonexistent")
        assert "error" in result

    def test_detect_all_tools(self, setup_handler: SetupHandler) -> None:
        """Test detecting all tools."""
        with patch("shutil.which", return_value=None):
            results = setup_handler.detect_all_tools()

            assert len(results) > 0
            for result in results:
                assert "tool_id" in result
                assert "name" in result
                assert "status" in result

    def test_detect_essential_tools(self, setup_handler: SetupHandler) -> None:
        """Test detecting essential tools."""
        with patch("shutil.which", return_value=None):
            results = setup_handler.detect_essential_tools()

            assert len(results) > 0


class TestSetupHandlerInstallMethods:
    """Tests for install methods."""

    def test_get_install_methods(self, setup_handler: SetupHandler) -> None:
        """Test getting install methods for a tool."""
        result = setup_handler.get_install_methods("git")

        assert result["tool_id"] == "git"
        assert "methods" in result
        assert len(result["methods"]) > 0

        for method in result["methods"]:
            assert "method" in method
            assert "available" in method
            assert "package" in method

    def test_get_install_methods_not_found(self, setup_handler: SetupHandler) -> None:
        """Test getting install methods for non-existent tool."""
        result = setup_handler.get_install_methods("nonexistent")
        assert "error" in result


class TestSetupHandlerSummary:
    """Tests for summary methods."""

    def test_get_prerequisites_summary(self, setup_handler: SetupHandler) -> None:
        """Test getting prerequisites summary."""
        with patch("shutil.which", return_value=None):
            summary = setup_handler.get_prerequisites_summary()

            assert "total" in summary
            assert "installed" in summary
            assert "not_installed" in summary
            assert "outdated" in summary
            assert "by_category" in summary

            assert summary["total"] > 0
            assert isinstance(summary["by_category"], dict)


class TestSetupHandlerInstallers:
    """Tests for installer methods."""

    def test_get_available_installers(self, setup_handler: SetupHandler) -> None:
        """Test getting available installers."""
        installers = setup_handler.get_available_installers()

        assert len(installers) > 0
        for installer in installers:
            assert "package_manager" in installer
            assert "name" in installer


class TestSetupHandlerMise:
    """Tests for Mise-related methods."""

    def test_check_mise_available_installed(self, setup_handler: SetupHandler) -> None:
        """Test checking Mise availability when installed."""
        with patch("shutil.which", return_value="/usr/local/bin/mise"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    stdout="mise 2024.1.0",
                    stderr="",
                )
                # Mock the async is_available
                with patch("asyncio.run") as mock_asyncio:
                    mock_asyncio.side_effect = [True, "2024.1.0"]
                    result = setup_handler.check_mise_available()

                    assert result["available"] is True

    def test_check_mise_available_not_installed(self, setup_handler: SetupHandler) -> None:
        """Test checking Mise availability when not installed."""
        with patch("asyncio.run") as mock_asyncio:
            mock_asyncio.return_value = False
            result = setup_handler.check_mise_available()

            assert result["available"] is False
            assert "install_hint" in result
