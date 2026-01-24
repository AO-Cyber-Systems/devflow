"""Tests for platform detection and abstraction."""

from unittest.mock import MagicMock, patch

import pytest

from devflow.core.platform import (
    CURRENT_PLATFORM,
    Platform,
    detect_platform,
    is_linux,
    is_macos,
    is_unix_like,
    is_windows,
    is_wsl,
    is_wsl2,
)


class TestPlatformDetection:
    """Tests for platform detection functions."""

    def test_detect_linux(self) -> None:
        """Test detection of native Linux."""
        with patch("platform.system", return_value="Linux"):
            mock_uname = MagicMock()
            mock_uname.release = "5.15.0-generic"
            with patch("platform.uname", return_value=mock_uname):
                result = detect_platform()
                assert result == Platform.LINUX

    def test_detect_wsl2_microsoft(self) -> None:
        """Test detection of WSL2 via microsoft in release."""
        with patch("platform.system", return_value="Linux"):
            mock_uname = MagicMock()
            mock_uname.release = "5.15.167.4-microsoft-standard-WSL2"
            with patch("platform.uname", return_value=mock_uname):
                result = detect_platform()
                assert result == Platform.WSL2

    def test_detect_wsl2_wsl(self) -> None:
        """Test detection of WSL2 via wsl in release."""
        with patch("platform.system", return_value="Linux"):
            mock_uname = MagicMock()
            mock_uname.release = "5.15.0-wsl-ubuntu"
            with patch("platform.uname", return_value=mock_uname):
                result = detect_platform()
                assert result == Platform.WSL2

    def test_detect_macos(self) -> None:
        """Test detection of macOS."""
        with patch("platform.system", return_value="Darwin"):
            result = detect_platform()
            assert result == Platform.MACOS

    def test_detect_windows(self) -> None:
        """Test detection of Windows."""
        with patch("platform.system", return_value="Windows"):
            result = detect_platform()
            assert result == Platform.WINDOWS

    def test_detect_unsupported(self) -> None:
        """Test that unsupported platforms raise RuntimeError."""
        with patch("platform.system", return_value="FreeBSD"):
            with pytest.raises(RuntimeError) as exc_info:
                detect_platform()
            assert "Unsupported platform" in str(exc_info.value)


class TestPlatformHelpers:
    """Tests for platform helper functions."""

    def test_is_wsl_on_linux(self) -> None:
        """Test is_wsl returns False on native Linux."""
        with patch("platform.system", return_value="Linux"):
            mock_uname = MagicMock()
            mock_uname.release = "5.15.0-generic"
            with patch("platform.uname", return_value=mock_uname):
                assert is_wsl() is False

    def test_is_wsl_on_wsl2(self) -> None:
        """Test is_wsl returns True on WSL2."""
        with patch("platform.system", return_value="Linux"):
            mock_uname = MagicMock()
            mock_uname.release = "5.15.167.4-microsoft-standard-WSL2"
            with patch("platform.uname", return_value=mock_uname):
                assert is_wsl() is True

    def test_is_wsl_on_windows(self) -> None:
        """Test is_wsl returns False on Windows."""
        with patch("platform.system", return_value="Windows"):
            assert is_wsl() is False

    def test_is_wsl2_on_wsl2(self) -> None:
        """Test is_wsl2 returns True on WSL2."""
        with patch("devflow.core.platform.detect_platform", return_value=Platform.WSL2):
            assert is_wsl2() is True

    def test_is_wsl2_on_linux(self) -> None:
        """Test is_wsl2 returns False on native Linux."""
        with patch("devflow.core.platform.detect_platform", return_value=Platform.LINUX):
            assert is_wsl2() is False

    def test_is_windows_on_windows(self) -> None:
        """Test is_windows returns True on Windows."""
        with patch("devflow.core.platform.detect_platform", return_value=Platform.WINDOWS):
            assert is_windows() is True

    def test_is_windows_on_linux(self) -> None:
        """Test is_windows returns False on Linux."""
        with patch("devflow.core.platform.detect_platform", return_value=Platform.LINUX):
            assert is_windows() is False

    def test_is_macos_on_macos(self) -> None:
        """Test is_macos returns True on macOS."""
        with patch("devflow.core.platform.detect_platform", return_value=Platform.MACOS):
            assert is_macos() is True

    def test_is_macos_on_linux(self) -> None:
        """Test is_macos returns False on Linux."""
        with patch("devflow.core.platform.detect_platform", return_value=Platform.LINUX):
            assert is_macos() is False

    def test_is_linux_on_linux(self) -> None:
        """Test is_linux returns True on native Linux."""
        with patch("devflow.core.platform.detect_platform", return_value=Platform.LINUX):
            assert is_linux() is True

    def test_is_linux_on_wsl2(self) -> None:
        """Test is_linux returns False on WSL2 (it's a separate platform)."""
        with patch("devflow.core.platform.detect_platform", return_value=Platform.WSL2):
            assert is_linux() is False

    def test_is_unix_like_on_linux(self) -> None:
        """Test is_unix_like returns True on Linux."""
        with patch("devflow.core.platform.detect_platform", return_value=Platform.LINUX):
            assert is_unix_like() is True

    def test_is_unix_like_on_macos(self) -> None:
        """Test is_unix_like returns True on macOS."""
        with patch("devflow.core.platform.detect_platform", return_value=Platform.MACOS):
            assert is_unix_like() is True

    def test_is_unix_like_on_wsl2(self) -> None:
        """Test is_unix_like returns True on WSL2."""
        with patch("devflow.core.platform.detect_platform", return_value=Platform.WSL2):
            assert is_unix_like() is True

    def test_is_unix_like_on_windows(self) -> None:
        """Test is_unix_like returns False on Windows."""
        with patch("devflow.core.platform.detect_platform", return_value=Platform.WINDOWS):
            assert is_unix_like() is False


class TestPlatformEnum:
    """Tests for Platform enum."""

    def test_platform_values(self) -> None:
        """Test Platform enum has expected values."""
        assert Platform.LINUX.value == "linux"
        assert Platform.MACOS.value == "darwin"
        assert Platform.WINDOWS.value == "windows"
        assert Platform.WSL2.value == "wsl2"

    def test_platform_members(self) -> None:
        """Test Platform enum has expected members."""
        members = list(Platform)
        assert len(members) == 4
        assert Platform.LINUX in members
        assert Platform.MACOS in members
        assert Platform.WINDOWS in members
        assert Platform.WSL2 in members


class TestCurrentPlatform:
    """Tests for the CURRENT_PLATFORM constant."""

    def test_current_platform_is_valid(self) -> None:
        """Test CURRENT_PLATFORM is a valid Platform enum value."""
        assert isinstance(CURRENT_PLATFORM, Platform)

    def test_current_platform_matches_detection(self) -> None:
        """Test CURRENT_PLATFORM matches what detect_platform would return."""
        # Note: This test will pass on the actual platform it's run on
        # We can't easily mock CURRENT_PLATFORM since it's computed at import time
        assert CURRENT_PLATFORM == detect_platform()
