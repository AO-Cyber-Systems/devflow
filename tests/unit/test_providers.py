"""Tests for provider implementations."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from devflow.core.config import GitHubAppConfig
from devflow.providers.docker import DockerProvider
from devflow.providers.github import GitHubAppProvider, GitHubProvider, resolve_github_app_config
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
        # Binary name is platform-specific
        expected_binary = "op.exe" if sys.platform == "win32" else "op"
        assert provider.binary == expected_binary

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


class TestGitHubAppProvider:
    """Tests for GitHub App authentication provider."""

    # Sample RSA private key for testing (DO NOT USE IN PRODUCTION)
    TEST_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA2mKqH0dSqmPRjlZxDXQusmVjAAr2y8jMQKMvVHGFDg6VJl9v
qSJHw2mfvmKJO8oB5L3u/9a3x4AXQ5z5yXW5yT5S3gLi5nnc7AAMk4mXP5szHU0I
kGPB0tC9Lur6eOBz+5F0QSMfX0Nz8yz0ZV8sVxYQ8L0EAj0L5h0X8M0v0M0G3a0X
Y5c7a0M0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0
a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0
a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0awIDAQABAoIBAFPY8q8m3Qw3M3NWVU8X
a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0
a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0
a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0
a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0X0a0E=
-----END RSA PRIVATE KEY-----"""

    def test_name(self) -> None:
        """Test provider name."""
        config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key=self.TEST_PRIVATE_KEY,
        )
        provider = GitHubAppProvider(config)
        assert provider.name == "github-app"

    @patch("devflow.providers.github.requests.post")
    @patch("devflow.providers.github.jwt.encode")
    def test_get_installation_token_success(self, mock_jwt_encode: MagicMock, mock_post: MagicMock) -> None:
        """Test successful installation token retrieval."""
        mock_jwt_encode.return_value = "mock_jwt_token"
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {
                "token": "ghs_test_token",
                "expires_at": "2026-01-22T12:00:00Z",
            },
        )

        config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key=self.TEST_PRIVATE_KEY,
        )
        provider = GitHubAppProvider(config)
        token = provider._get_installation_token()

        assert token == "ghs_test_token"
        mock_post.assert_called_once()

    @patch("devflow.providers.github.requests.post")
    @patch("devflow.providers.github.jwt.encode")
    def test_get_installation_token_failure(self, mock_jwt_encode: MagicMock, mock_post: MagicMock) -> None:
        """Test failed installation token retrieval."""
        mock_jwt_encode.return_value = "mock_jwt_token"
        mock_post.return_value = MagicMock(
            status_code=401,
            text="Bad credentials",
        )

        config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key=self.TEST_PRIVATE_KEY,
        )
        provider = GitHubAppProvider(config)

        with pytest.raises(RuntimeError, match="Failed to get installation token"):
            provider._get_installation_token()

    @patch("devflow.providers.github.requests.post")
    @patch("devflow.providers.github.jwt.encode")
    def test_is_authenticated_success(self, mock_jwt_encode: MagicMock, mock_post: MagicMock) -> None:
        """Test successful authentication check."""
        mock_jwt_encode.return_value = "mock_jwt_token"
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {
                "token": "ghs_test_token",
                "expires_at": "2026-01-22T12:00:00Z",
            },
        )

        config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key=self.TEST_PRIVATE_KEY,
        )
        provider = GitHubAppProvider(config)
        assert provider.is_authenticated() is True

    @patch("devflow.providers.github.requests.post")
    @patch("devflow.providers.github.jwt.encode")
    def test_is_authenticated_failure(self, mock_jwt_encode: MagicMock, mock_post: MagicMock) -> None:
        """Test failed authentication check."""
        mock_jwt_encode.return_value = "mock_jwt_token"
        mock_post.return_value = MagicMock(
            status_code=401,
            text="Bad credentials",
        )

        config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key=self.TEST_PRIVATE_KEY,
        )
        provider = GitHubAppProvider(config)
        assert provider.is_authenticated() is False

    @patch("devflow.providers.github.requests.get")
    @patch("devflow.providers.github.requests.post")
    @patch("devflow.providers.github.jwt.encode")
    def test_list_secrets_success(self, mock_jwt_encode: MagicMock, mock_post: MagicMock, mock_get: MagicMock) -> None:
        """Test successful secrets listing."""
        mock_jwt_encode.return_value = "mock_jwt_token"
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {
                "token": "ghs_test_token",
                "expires_at": "2026-01-22T12:00:00Z",
            },
        )
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "total_count": 2,
                "secrets": [
                    {"name": "DATABASE_URL", "created_at": "2025-01-01T00:00:00Z"},
                    {"name": "API_KEY", "created_at": "2025-01-01T00:00:00Z"},
                ],
            },
        )

        config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key=self.TEST_PRIVATE_KEY,
        )
        provider = GitHubAppProvider(config)
        secrets = provider.list_secrets("owner/repo")

        assert secrets == ["DATABASE_URL", "API_KEY"]

    @patch("devflow.providers.github.requests.get")
    @patch("devflow.providers.github.requests.put")
    @patch("devflow.providers.github.requests.post")
    @patch("devflow.providers.github.jwt.encode")
    def test_set_secret_success(
        self,
        mock_jwt_encode: MagicMock,
        mock_post: MagicMock,
        mock_put: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        """Test successful secret setting."""
        mock_jwt_encode.return_value = "mock_jwt_token"
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {
                "token": "ghs_test_token",
                "expires_at": "2026-01-22T12:00:00Z",
            },
        )
        # Mock public key response
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "key_id": "test_key_id",
                "key": "hBT5WZEj8gF3P8A2tGr8oPrQ6HdM0ZsyZ5xz1j5nWwI=",
            },
        )
        mock_put.return_value = MagicMock(status_code=201)

        config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key=self.TEST_PRIVATE_KEY,
        )
        provider = GitHubAppProvider(config)

        with patch.object(provider, "_encrypt_secret", return_value="encrypted_value"):
            result = provider.set_secret("owner/repo", "TEST_SECRET", "secret_value")

        assert result is True
        mock_put.assert_called_once()

    @patch("devflow.providers.github.requests.delete")
    @patch("devflow.providers.github.requests.post")
    @patch("devflow.providers.github.jwt.encode")
    def test_delete_secret_success(
        self, mock_jwt_encode: MagicMock, mock_post: MagicMock, mock_delete: MagicMock
    ) -> None:
        """Test successful secret deletion."""
        mock_jwt_encode.return_value = "mock_jwt_token"
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {
                "token": "ghs_test_token",
                "expires_at": "2026-01-22T12:00:00Z",
            },
        )
        mock_delete.return_value = MagicMock(status_code=204)

        config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key=self.TEST_PRIVATE_KEY,
        )
        provider = GitHubAppProvider(config)
        result = provider.delete_secret("owner/repo", "TEST_SECRET")

        assert result is True
        mock_delete.assert_called_once()

    @patch("devflow.providers.github.requests.post")
    @patch("devflow.providers.github.jwt.encode")
    def test_token_caching(self, mock_jwt_encode: MagicMock, mock_post: MagicMock) -> None:
        """Test that installation tokens are cached and reused."""
        mock_jwt_encode.return_value = "mock_jwt_token"
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {
                "token": "ghs_test_token",
                "expires_at": "2026-12-31T23:59:59Z",
            },
        )

        config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key=self.TEST_PRIVATE_KEY,
        )
        provider = GitHubAppProvider(config)

        # First call should fetch the token
        token1 = provider._get_installation_token()
        # Second call should use cached token
        token2 = provider._get_installation_token()

        assert token1 == token2
        # POST should only be called once (for the first token fetch)
        assert mock_post.call_count == 1


class TestResolveGitHubAppConfig:
    """Tests for GitHub App config resolution with 1Password references."""

    def test_resolve_non_op_values(self) -> None:
        """Test that non-op:// values are passed through unchanged."""
        config = GitHubAppConfig(
            app_id="12345",
            installation_id="67890",
            private_key="raw_private_key",
        )
        resolved = resolve_github_app_config(config)

        assert resolved.app_id == "12345"
        assert resolved.installation_id == "67890"
        assert resolved.private_key == "raw_private_key"

    @patch("devflow.providers.onepassword.OnePasswordProvider")
    def test_resolve_op_references(self, mock_op_class: MagicMock) -> None:
        """Test that op:// references are resolved via 1Password."""
        mock_op = MagicMock()
        mock_op.is_authenticated.return_value = True
        mock_op.inject.side_effect = lambda x: {
            "op://vault/item/app_id": "resolved_app_id",
            "op://vault/item/installation_id": "resolved_installation_id",
            "op://vault/item/private_key": "resolved_private_key",
        }.get(x, x)
        mock_op_class.return_value = mock_op

        config = GitHubAppConfig(
            app_id="op://vault/item/app_id",
            installation_id="op://vault/item/installation_id",
            private_key="op://vault/item/private_key",
        )
        resolved = resolve_github_app_config(config)

        assert resolved.app_id == "resolved_app_id"
        assert resolved.installation_id == "resolved_installation_id"
        assert resolved.private_key == "resolved_private_key"

    @patch("devflow.providers.onepassword.OnePasswordProvider")
    def test_resolve_op_not_authenticated(self, mock_op_class: MagicMock) -> None:
        """Test that error is raised when 1Password is not authenticated."""
        mock_op = MagicMock()
        mock_op.is_authenticated.return_value = False
        mock_op_class.return_value = mock_op

        config = GitHubAppConfig(
            app_id="op://vault/item/app_id",
            installation_id="67890",
            private_key="raw_key",
        )

        with pytest.raises(ValueError, match="1Password not authenticated"):
            resolve_github_app_config(config)

    @patch("devflow.providers.onepassword.OnePasswordProvider")
    def test_resolve_op_injection_failure(self, mock_op_class: MagicMock) -> None:
        """Test that error is raised when 1Password injection fails."""
        mock_op = MagicMock()
        mock_op.is_authenticated.return_value = True
        # Return the same value (injection failed)
        mock_op.inject.side_effect = lambda x: x
        mock_op_class.return_value = mock_op

        config = GitHubAppConfig(
            app_id="op://vault/item/app_id",
            installation_id="67890",
            private_key="raw_key",
        )

        with pytest.raises(ValueError, match="Failed to read from 1Password"):
            resolve_github_app_config(config)
