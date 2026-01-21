"""Tests for provider implementations."""

import shutil
from unittest.mock import MagicMock, patch

import pytest

from devflow.providers.base import Provider
from devflow.providers.docker import DockerProvider
from devflow.providers.github import GitHubProvider
from devflow.providers.onepassword import OnePasswordProvider


class TestGitHubProvider:
    """Tests for GitHub CLI provider."""

    def test_name_and_binary(self) -> None:
        """Test provider name and binary."""
        provider = GitHubProvider()
        assert provider.name == "github"
        assert provider.binary == "gh"

    def test_is_available(self) -> None:
        """Test availability check."""
        provider = GitHubProvider()
        # This depends on gh being installed
        result = provider.is_available()
        assert isinstance(result, bool)

    @patch("subprocess.run")
    def test_is_authenticated_success(self, mock_run: MagicMock) -> None:
        """Test successful authentication check."""
        mock_run.return_value = MagicMock(returncode=0)

        provider = GitHubProvider()
        with patch.object(provider, "is_available", return_value=True):
            result = provider.is_authenticated()
            assert result is True

    @patch("subprocess.run")
    def test_is_authenticated_failure(self, mock_run: MagicMock) -> None:
        """Test failed authentication check."""
        mock_run.return_value = MagicMock(returncode=1)

        provider = GitHubProvider()
        with patch.object(provider, "is_available", return_value=True):
            result = provider.is_authenticated()
            assert result is False


class TestDockerProvider:
    """Tests for Docker provider."""

    def test_name_and_binary(self) -> None:
        """Test provider name and binary."""
        provider = DockerProvider()
        assert provider.name == "docker"
        assert provider.binary == "docker"

    def test_is_available(self) -> None:
        """Test availability check."""
        provider = DockerProvider()
        result = provider.is_available()
        assert isinstance(result, bool)

    def test_doctor_output(self) -> None:
        """Test doctor output format."""
        provider = DockerProvider()
        status = provider.doctor()

        assert "name" in status
        assert "binary" in status
        assert "available" in status
        assert "authenticated" in status
        assert status["name"] == "docker"
        assert status["binary"] == "docker"


class TestOnePasswordProvider:
    """Tests for 1Password CLI provider."""

    def test_name_and_binary(self) -> None:
        """Test provider name and binary."""
        provider = OnePasswordProvider()
        assert provider.name == "1password"
        assert provider.binary == "op"

    def test_is_available(self) -> None:
        """Test availability check."""
        provider = OnePasswordProvider()
        result = provider.is_available()
        assert isinstance(result, bool)
