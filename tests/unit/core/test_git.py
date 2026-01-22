"""Tests for git utilities."""

from unittest.mock import MagicMock, patch

from devflow.core.git import configure_git_user, get_co_author_line


class TestConfigureGitUser:
    """Tests for configure_git_user function."""

    def test_skips_when_no_config(self) -> None:
        """Test skips when no git user configured."""
        config = MagicMock()
        config.git.user.name = None
        config.git.user.email = None

        result = configure_git_user(config)

        assert result["status"] == "skipped"
        assert "No git user config specified" in result["message"]

    @patch("devflow.core.git.subprocess.run")
    def test_configures_name_only(self, mock_run: MagicMock) -> None:
        """Test configures only name when email not set."""
        config = MagicMock()
        config.git.user.name = "Test User"
        config.git.user.email = None

        result = configure_git_user(config)

        assert result["status"] == "ok"
        assert "name=Test User" in result["message"]
        mock_run.assert_called_once_with(
            ["git", "config", "--local", "user.name", "Test User"],
            capture_output=True,
        )

    @patch("devflow.core.git.subprocess.run")
    def test_configures_email_only(self, mock_run: MagicMock) -> None:
        """Test configures only email when name not set."""
        config = MagicMock()
        config.git.user.name = None
        config.git.user.email = "test@example.com"

        result = configure_git_user(config)

        assert result["status"] == "ok"
        assert "email=test@example.com" in result["message"]
        mock_run.assert_called_once_with(
            ["git", "config", "--local", "user.email", "test@example.com"],
            capture_output=True,
        )

    @patch("devflow.core.git.subprocess.run")
    def test_configures_both(self, mock_run: MagicMock) -> None:
        """Test configures both name and email."""
        config = MagicMock()
        config.git.user.name = "Test User"
        config.git.user.email = "test@example.com"

        result = configure_git_user(config)

        assert result["status"] == "ok"
        assert "name=Test User" in result["message"]
        assert "email=test@example.com" in result["message"]
        assert mock_run.call_count == 2


class TestGetCoAuthorLine:
    """Tests for get_co_author_line function."""

    def test_returns_line_when_enabled(self) -> None:
        """Test returns co-author line when enabled."""
        config = MagicMock()
        config.git.co_author.enabled = True
        config.git.co_author.name = "Claude"
        config.git.co_author.email = "noreply@anthropic.com"

        result = get_co_author_line(config)

        assert result == "Co-Authored-By: Claude <noreply@anthropic.com>"

    def test_returns_none_when_disabled(self) -> None:
        """Test returns None when disabled."""
        config = MagicMock()
        config.git.co_author.enabled = False

        result = get_co_author_line(config)

        assert result is None

    def test_uses_custom_values(self) -> None:
        """Test uses custom name and email."""
        config = MagicMock()
        config.git.co_author.enabled = True
        config.git.co_author.name = "AI Assistant"
        config.git.co_author.email = "ai@company.com"

        result = get_co_author_line(config)

        assert result == "Co-Authored-By: AI Assistant <ai@company.com>"
