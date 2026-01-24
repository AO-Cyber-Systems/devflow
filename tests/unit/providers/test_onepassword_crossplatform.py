"""Cross-platform tests for 1Password provider."""

from unittest.mock import patch

from devflow.core.platform import Platform
from devflow.providers.onepassword import OnePasswordProvider


class TestOnePasswordProviderBinary:
    """Tests for 1Password binary name across platforms."""

    def test_binary_name_on_linux(self) -> None:
        """Test 1Password binary name on Linux."""
        with patch("devflow.providers.onepassword.CURRENT_PLATFORM", Platform.LINUX):
            provider = OnePasswordProvider()
            assert provider.binary == "op"

    def test_binary_name_on_macos(self) -> None:
        """Test 1Password binary name on macOS."""
        with patch("devflow.providers.onepassword.CURRENT_PLATFORM", Platform.MACOS):
            provider = OnePasswordProvider()
            assert provider.binary == "op"

    def test_binary_name_on_wsl2(self) -> None:
        """Test 1Password binary name on WSL2."""
        with patch("devflow.providers.onepassword.CURRENT_PLATFORM", Platform.WSL2):
            provider = OnePasswordProvider()
            assert provider.binary == "op"

    def test_binary_name_on_windows(self) -> None:
        """Test 1Password binary name on Windows."""
        with patch("devflow.providers.onepassword.CURRENT_PLATFORM", Platform.WINDOWS):
            provider = OnePasswordProvider()
            assert provider.binary == "op.exe"


class TestOnePasswordProviderName:
    """Tests for provider name."""

    def test_provider_name(self) -> None:
        """Test provider name is correct."""
        provider = OnePasswordProvider()
        assert provider.name == "1password"
