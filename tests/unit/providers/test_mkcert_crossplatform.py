"""Cross-platform tests for mkcert provider."""

import os
from pathlib import Path
from unittest.mock import patch

from devflow.core.platform import Platform
from devflow.providers.mkcert import MkcertProvider


class TestMkcertProviderBinary:
    """Tests for mkcert binary name across platforms."""

    def test_binary_name_on_linux(self) -> None:
        """Test mkcert binary name on Linux."""
        with patch("devflow.providers.mkcert.CURRENT_PLATFORM", Platform.LINUX):
            provider = MkcertProvider()
            assert provider.binary == "mkcert"

    def test_binary_name_on_macos(self) -> None:
        """Test mkcert binary name on macOS."""
        with patch("devflow.providers.mkcert.CURRENT_PLATFORM", Platform.MACOS):
            provider = MkcertProvider()
            assert provider.binary == "mkcert"

    def test_binary_name_on_wsl2(self) -> None:
        """Test mkcert binary name on WSL2."""
        with patch("devflow.providers.mkcert.CURRENT_PLATFORM", Platform.WSL2):
            provider = MkcertProvider()
            assert provider.binary == "mkcert"

    def test_binary_name_on_windows(self) -> None:
        """Test mkcert binary name on Windows."""
        with patch("devflow.providers.mkcert.CURRENT_PLATFORM", Platform.WINDOWS):
            provider = MkcertProvider()
            assert provider.binary == "mkcert.exe"


class TestMkcertProviderCertDir:
    """Tests for certificate directory resolution across platforms."""

    def test_cert_dir_on_linux(self) -> None:
        """Test certificate directory on Linux."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            provider = MkcertProvider()
            cert_dir = provider.get_default_cert_dir()
            assert cert_dir == Path.home() / ".local" / "share" / "mkcert"

    def test_cert_dir_on_macos(self) -> None:
        """Test certificate directory on macOS."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.MACOS):
            provider = MkcertProvider()
            cert_dir = provider.get_default_cert_dir()
            assert cert_dir == Path.home() / "Library" / "Application Support" / "mkcert"

    def test_cert_dir_on_wsl2(self) -> None:
        """Test certificate directory on WSL2."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WSL2):
            provider = MkcertProvider()
            cert_dir = provider.get_default_cert_dir()
            assert cert_dir == Path.home() / ".local" / "share" / "mkcert"

    def test_cert_dir_on_windows(self) -> None:
        """Test certificate directory on Windows."""
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            with patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\Test\\AppData\\Local"}):
                provider = MkcertProvider()
                cert_dir = provider.get_default_cert_dir()
                assert cert_dir == Path("C:\\Users\\Test\\AppData\\Local") / "mkcert"


class TestMkcertProviderAvailability:
    """Tests for mkcert availability checking across platforms."""

    def test_is_available_checks_binary(self) -> None:
        """Test is_available checks for binary existence."""
        with patch("devflow.providers.mkcert.CURRENT_PLATFORM", Platform.LINUX):
            with patch("shutil.which", return_value="/usr/bin/mkcert"):
                provider = MkcertProvider()
                assert provider.is_available() is True

    def test_is_available_returns_false_when_not_found(self) -> None:
        """Test is_available returns False when binary not found."""
        with patch("devflow.providers.mkcert.CURRENT_PLATFORM", Platform.LINUX):
            with patch("shutil.which", return_value=None):
                provider = MkcertProvider()
                assert provider.is_available() is False

    def test_is_available_on_windows_checks_both_names(self) -> None:
        """Test is_available on Windows checks both mkcert and mkcert.exe."""
        with patch("devflow.providers.mkcert.CURRENT_PLATFORM", Platform.WINDOWS):
            # First call for mkcert.exe returns None, second for mkcert returns path
            def which_side_effect(name):
                if name == "mkcert.exe":
                    return None
                if name == "mkcert":
                    return "C:\\mkcert\\mkcert"
                return None

            with patch("shutil.which", side_effect=which_side_effect):
                provider = MkcertProvider()
                assert provider.is_available() is True


class TestMkcertProviderName:
    """Tests for provider name."""

    def test_provider_name(self) -> None:
        """Test provider name is correct."""
        provider = MkcertProvider()
        assert provider.name == "mkcert"
