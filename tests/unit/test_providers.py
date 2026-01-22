"""Tests for provider implementations."""

from unittest.mock import MagicMock, patch

from devflow.providers.docker import DockerProvider
from devflow.providers.github import GitHubProvider
from devflow.providers.onepassword import OnePasswordProvider
from devflow.providers.supabase import SupabaseProvider


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


class TestSupabaseProvider:
    """Tests for Supabase CLI provider."""

    def test_name_and_binary(self) -> None:
        """Test provider name and binary."""
        provider = SupabaseProvider()
        assert provider.name == "supabase"
        assert provider.binary == "supabase"

    def test_is_available(self) -> None:
        """Test availability check."""
        provider = SupabaseProvider()
        result = provider.is_available()
        assert isinstance(result, bool)

    def test_is_authenticated_self_hosted(self) -> None:
        """Test that self-hosted auth just checks availability."""
        provider = SupabaseProvider()
        with patch.object(provider, "is_available", return_value=True):
            assert provider.is_authenticated() is True

        with patch.object(provider, "is_available", return_value=False):
            assert provider.is_authenticated() is False

    @patch("subprocess.run")
    def test_db_push_success(self, mock_run: MagicMock) -> None:
        """Test successful db push."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Applied migration 20240101000000_initial.sql\nApplied migration 20240102000000_add_email.sql",
            stderr="",
        )

        provider = SupabaseProvider()
        with patch.object(provider, "is_available", return_value=True):
            result = provider.db_push(
                db_url="postgresql://localhost:5432/test",
                migrations_dir="supabase/migrations",
            )

        assert result.success is True
        assert result.applied_count == 2
        assert "2 migration" in result.message

    @patch("subprocess.run")
    def test_db_push_failure(self, mock_run: MagicMock) -> None:
        """Test failed db push."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: migration failed",
        )

        provider = SupabaseProvider()
        with patch.object(provider, "is_available", return_value=True):
            result = provider.db_push(
                db_url="postgresql://localhost:5432/test",
                migrations_dir="supabase/migrations",
            )

        assert result.success is False
        assert "failed" in result.error.lower()

    def test_db_push_not_available(self) -> None:
        """Test db push when CLI not installed."""
        provider = SupabaseProvider()
        with patch.object(provider, "is_available", return_value=False):
            result = provider.db_push(
                db_url="postgresql://localhost:5432/test",
                migrations_dir="supabase/migrations",
            )

        assert result.success is False
        assert "not installed" in result.message.lower()

    @patch("subprocess.run")
    def test_db_diff_has_changes(self, mock_run: MagicMock) -> None:
        """Test db diff with schema changes."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ALTER TABLE users ADD COLUMN age INTEGER;",
            stderr="",
        )

        provider = SupabaseProvider()
        with patch.object(provider, "is_available", return_value=True):
            result = provider.db_diff(
                db_url="postgresql://localhost:5432/test",
                migrations_dir="supabase/migrations",
            )

        assert result.has_changes is True
        assert "ALTER TABLE" in result.diff_sql

    @patch("subprocess.run")
    def test_db_diff_no_changes(self, mock_run: MagicMock) -> None:
        """Test db diff with no schema changes."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="-- No changes",
            stderr="",
        )

        provider = SupabaseProvider()
        with patch.object(provider, "is_available", return_value=True):
            result = provider.db_diff(
                db_url="postgresql://localhost:5432/test",
                migrations_dir="supabase/migrations",
            )

        assert result.has_changes is False

    def test_doctor_output(self) -> None:
        """Test doctor output format."""
        provider = SupabaseProvider()
        status = provider.doctor()

        assert "name" in status
        assert "binary" in status
        assert "available" in status
        assert "authenticated" in status
        assert status["name"] == "supabase"
        assert status["binary"] == "supabase"
