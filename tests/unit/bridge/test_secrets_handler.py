"""Tests for secrets bridge handler."""

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestSecretsHandlerList:
    """Tests for SecretsHandler.list()."""

    @patch("bridge.handlers.secrets.load_project_config")
    def test_list_no_config(self, mock_load: MagicMock) -> None:
        """Test list when no config found."""
        from bridge.handlers.secrets import SecretsHandler

        mock_load.return_value = None

        handler = SecretsHandler()
        result = handler.list("/some/path")

        assert "error" in result
        assert "devflow.yml" in result["error"]

    @patch("bridge.handlers.secrets.load_project_config")
    def test_list_no_secrets_config(self, mock_load: MagicMock) -> None:
        """Test list when no secrets section in config."""
        from bridge.handlers.secrets import SecretsHandler

        mock_config = MagicMock()
        mock_config.secrets = None
        mock_load.return_value = mock_config

        handler = SecretsHandler()
        result = handler.list("/some/path")

        assert "error" in result
        assert "secrets" in result["error"].lower()

    @patch("bridge.handlers.secrets.load_project_config")
    def test_list_success(self, mock_load: MagicMock) -> None:
        """Test successful list."""
        from bridge.handlers.secrets import SecretsHandler

        mock_mapping1 = MagicMock()
        mock_mapping1.name = "db-password"
        mock_mapping1.op_item = "Database"
        mock_mapping1.github_secret = "DB_PASSWORD"
        mock_mapping1.docker_secret = "db_password"

        mock_mapping2 = MagicMock()
        mock_mapping2.name = "api-key"
        mock_mapping2.op_item = "API"
        mock_mapping2.github_secret = None
        mock_mapping2.docker_secret = None

        mock_config = MagicMock()
        mock_config.secrets.mappings = [mock_mapping1, mock_mapping2]
        mock_load.return_value = mock_config

        handler = SecretsHandler()
        result = handler.list("/some/path")

        assert result["total_count"] == 2
        assert result["mapped_count"] == 2
        assert len(result["secrets"]) == 2

    @patch("bridge.handlers.secrets.load_project_config")
    def test_list_with_filter(self, mock_load: MagicMock) -> None:
        """Test list with source filter."""
        from bridge.handlers.secrets import SecretsHandler

        mock_mapping1 = MagicMock()
        mock_mapping1.name = "db-password"
        mock_mapping1.op_item = "Database"
        mock_mapping1.github_secret = "DB_PASSWORD"
        mock_mapping1.docker_secret = None

        mock_mapping2 = MagicMock()
        mock_mapping2.name = "docker-secret"
        mock_mapping2.op_item = None
        mock_mapping2.github_secret = None
        mock_mapping2.docker_secret = "my_docker_secret"

        mock_config = MagicMock()
        mock_config.secrets.mappings = [mock_mapping1, mock_mapping2]
        mock_load.return_value = mock_config

        handler = SecretsHandler()
        result = handler.list("/some/path", source="github")

        assert len(result["secrets"]) == 1
        assert result["secrets"][0]["name"] == "db-password"


class TestSecretsHandlerSync:
    """Tests for SecretsHandler.sync()."""

    @patch("bridge.handlers.secrets.load_project_config")
    def test_sync_no_op_auth(self, mock_load: MagicMock) -> None:
        """Test sync when 1Password not authenticated."""
        from bridge.handlers.secrets import SecretsHandler

        mock_config = MagicMock()
        mock_config.secrets.vault = "Test"
        mock_load.return_value = mock_config

        handler = SecretsHandler()
        handler._onepassword = MagicMock()
        handler._onepassword.is_authenticated.return_value = False

        result = handler.sync("/some/path", "1password", "github")

        assert result["success"] is False
        assert "1Password" in result["error"]

    @patch("bridge.handlers.secrets.load_project_config")
    def test_sync_dry_run(self, mock_load: MagicMock) -> None:
        """Test sync with dry_run flag."""
        from bridge.handlers.secrets import SecretsHandler

        mock_mapping = MagicMock()
        mock_mapping.name = "db-password"
        mock_mapping.op_item = "Database"
        mock_mapping.op_field = "password"
        mock_mapping.github_secret = "DB_PASSWORD"
        mock_mapping.docker_secret = None

        mock_config = MagicMock()
        mock_config.secrets.vault = "Test"
        mock_config.secrets.mappings = [mock_mapping]
        mock_config.secrets.github = None
        mock_load.return_value = mock_config

        handler = SecretsHandler()
        handler._onepassword = MagicMock()
        handler._onepassword.is_authenticated.return_value = True
        handler._github = MagicMock()
        handler._github.is_authenticated.return_value = True

        with patch.object(handler, "_get_repo_name", return_value="test-org/test-repo"):
            result = handler.sync("/some/path", "1password", "github", dry_run=True)

        assert result["success"] is True
        assert result["dry_run"] is True
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "would_sync"

    @patch("bridge.handlers.secrets.load_project_config")
    def test_sync_to_github_success(self, mock_load: MagicMock) -> None:
        """Test successful sync to GitHub."""
        from bridge.handlers.secrets import SecretsHandler

        mock_mapping = MagicMock()
        mock_mapping.name = "db-password"
        mock_mapping.op_item = "Database"
        mock_mapping.op_field = "password"
        mock_mapping.github_secret = "DB_PASSWORD"
        mock_mapping.docker_secret = None

        mock_config = MagicMock()
        mock_config.secrets.vault = "Test"
        mock_config.secrets.mappings = [mock_mapping]
        mock_config.secrets.github = None
        mock_load.return_value = mock_config

        handler = SecretsHandler()
        handler._onepassword = MagicMock()
        handler._onepassword.is_authenticated.return_value = True
        handler._onepassword.read_field.return_value = "secret-value"
        handler._github = MagicMock()
        handler._github.is_authenticated.return_value = True
        handler._github.set_secret.return_value = True

        with patch.object(handler, "_get_repo_name", return_value="test-org/test-repo"):
            result = handler.sync("/some/path", "1password", "github")

        assert result["success"] is True
        assert result["synced"] == 1
        handler._github.set_secret.assert_called_once()

    @patch("bridge.handlers.secrets.load_project_config")
    def test_sync_to_docker_success(self, mock_load: MagicMock) -> None:
        """Test successful sync to Docker."""
        from bridge.handlers.secrets import SecretsHandler

        mock_mapping = MagicMock()
        mock_mapping.name = "db-password"
        mock_mapping.op_item = "Database"
        mock_mapping.op_field = "password"
        mock_mapping.github_secret = None
        mock_mapping.docker_secret = "db_password"

        mock_config = MagicMock()
        mock_config.secrets.vault = "Test"
        mock_config.secrets.mappings = [mock_mapping]
        mock_load.return_value = mock_config

        handler = SecretsHandler()
        handler._onepassword = MagicMock()
        handler._onepassword.is_authenticated.return_value = True
        handler._onepassword.read_field.return_value = "secret-value"
        handler._docker = MagicMock()
        handler._docker.is_authenticated.return_value = True
        handler._docker.secret_exists.return_value = False
        handler._docker.create_secret.return_value = True

        result = handler.sync("/some/path", "1password", "docker")

        assert result["success"] is True
        assert result["synced"] == 1
        handler._docker.create_secret.assert_called_once_with("db_password", "secret-value")


class TestSecretsHandlerVerify:
    """Tests for SecretsHandler.verify()."""

    @patch("bridge.handlers.secrets.load_project_config")
    def test_verify_all_in_sync(self, mock_load: MagicMock) -> None:
        """Test verify when all secrets are in sync."""
        from bridge.handlers.secrets import SecretsHandler

        mock_mapping = MagicMock()
        mock_mapping.name = "db-password"
        mock_mapping.op_item = "Database"
        mock_mapping.op_field = "password"
        mock_mapping.github_secret = "DB_PASSWORD"
        mock_mapping.docker_secret = "db_password"

        mock_config = MagicMock()
        mock_config.secrets.vault = "Test"
        mock_config.secrets.mappings = [mock_mapping]
        mock_config.secrets.github = None
        mock_load.return_value = mock_config

        handler = SecretsHandler()
        handler._onepassword = MagicMock()
        handler._onepassword.is_authenticated.return_value = True
        handler._onepassword.read_field.return_value = "secret-value"
        handler._github = MagicMock()
        handler._github.list_secrets.return_value = ["DB_PASSWORD"]
        handler._docker = MagicMock()
        handler._docker.is_authenticated.return_value = True
        handler._docker.list_secrets.return_value = [{"Name": "db_password"}]

        with patch.object(handler, "_get_repo_name", return_value="test-org/test-repo"):
            result = handler.verify("/some/path")

        assert result["success"] is True
        assert result["in_sync"] == 1
        assert result["out_of_sync"] == 0

    @patch("bridge.handlers.secrets.load_project_config")
    def test_verify_out_of_sync(self, mock_load: MagicMock) -> None:
        """Test verify when secrets are out of sync."""
        from bridge.handlers.secrets import SecretsHandler

        mock_mapping = MagicMock()
        mock_mapping.name = "db-password"
        mock_mapping.op_item = "Database"
        mock_mapping.op_field = "password"
        mock_mapping.github_secret = "DB_PASSWORD"
        mock_mapping.docker_secret = None

        mock_config = MagicMock()
        mock_config.secrets.vault = "Test"
        mock_config.secrets.mappings = [mock_mapping]
        mock_config.secrets.github = None
        mock_load.return_value = mock_config

        handler = SecretsHandler()
        handler._onepassword = MagicMock()
        handler._onepassword.is_authenticated.return_value = True
        handler._onepassword.read_field.return_value = "secret-value"
        handler._github = MagicMock()
        handler._github.list_secrets.return_value = []  # Secret not in GitHub
        handler._docker = MagicMock()
        handler._docker.is_authenticated.return_value = True
        handler._docker.list_secrets.return_value = []

        with patch.object(handler, "_get_repo_name", return_value="test-org/test-repo"):
            result = handler.verify("/some/path")

        assert result["success"] is True
        assert result["out_of_sync"] == 1


class TestSecretsHandlerExport:
    """Tests for SecretsHandler.export()."""

    @patch("bridge.handlers.secrets.load_project_config")
    def test_export_non_local_blocked(self, mock_load: MagicMock) -> None:
        """Test export is blocked for non-local environments."""
        from bridge.handlers.secrets import SecretsHandler

        mock_config = MagicMock()
        mock_config.secrets.vault = "Test"
        mock_load.return_value = mock_config

        handler = SecretsHandler()
        result = handler.export("/some/path", "production")

        assert result["success"] is False
        assert "local" in result["error"]

    @patch("bridge.handlers.secrets.load_project_config")
    def test_export_env_format(self, mock_load: MagicMock) -> None:
        """Test export in env format."""
        from bridge.handlers.secrets import SecretsHandler

        mock_mapping = MagicMock()
        mock_mapping.name = "db-password"
        mock_mapping.op_item = "Database"
        mock_mapping.op_field = "password"

        mock_config = MagicMock()
        mock_config.secrets.vault = "Test"
        mock_config.secrets.mappings = [mock_mapping]
        mock_load.return_value = mock_config

        handler = SecretsHandler()
        handler._onepassword = MagicMock()
        handler._onepassword.is_authenticated.return_value = True
        handler._onepassword.read_field.return_value = "my-secret-value"

        result = handler.export("/some/path", "local", format="env")

        assert result["success"] is True
        assert result["exported"] == 1
        assert 'DB_PASSWORD="my-secret-value"' in result["content"]

    @patch("bridge.handlers.secrets.load_project_config")
    def test_export_json_format(self, mock_load: MagicMock) -> None:
        """Test export in JSON format."""
        from bridge.handlers.secrets import SecretsHandler

        mock_mapping = MagicMock()
        mock_mapping.name = "db-password"
        mock_mapping.op_item = "Database"
        mock_mapping.op_field = "password"

        mock_config = MagicMock()
        mock_config.secrets.vault = "Test"
        mock_config.secrets.mappings = [mock_mapping]
        mock_load.return_value = mock_config

        handler = SecretsHandler()
        handler._onepassword = MagicMock()
        handler._onepassword.is_authenticated.return_value = True
        handler._onepassword.read_field.return_value = "my-secret-value"

        result = handler.export("/some/path", "local", format="json")

        assert result["success"] is True
        assert result["format"] == "json"
        assert "DB_PASSWORD" in result["content"]


class TestSecretsHandlerProviders:
    """Tests for SecretsHandler.providers()."""

    def test_providers_all_available(self) -> None:
        """Test providers when all are available."""
        from bridge.handlers.secrets import SecretsHandler

        handler = SecretsHandler()
        handler._onepassword = MagicMock()
        handler._onepassword.is_available.return_value = True
        handler._onepassword.is_authenticated.return_value = True
        handler._github = MagicMock()
        handler._github.is_available.return_value = True
        handler._github.is_authenticated.return_value = True
        handler._docker = MagicMock()
        handler._docker.is_available.return_value = True

        result = handler.providers()

        assert len(result["providers"]) == 4

        op = next(p for p in result["providers"] if p["name"] == "1password")
        assert op["available"] is True
        assert op["authenticated"] is True

        gh = next(p for p in result["providers"] if p["name"] == "github")
        assert gh["available"] is True

        docker = next(p for p in result["providers"] if p["name"] == "docker")
        assert docker["available"] is True

        env = next(p for p in result["providers"] if p["name"] == "env")
        assert env["available"] is True
        assert env["authenticated"] is True


class TestSecretsHandlerHelpers:
    """Tests for SecretsHandler helper methods."""

    def test_get_repo_name_ssh(self, tmp_path: Path) -> None:
        """Test getting repo name from SSH URL."""
        from bridge.handlers.secrets import SecretsHandler

        # Create a git repo with SSH remote
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text(
            """[remote "origin"]
        url = git@github.com:test-org/test-repo.git
"""
        )

        handler = SecretsHandler()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="git@github.com:test-org/test-repo.git\n",
            )
            result = handler._get_repo_name(tmp_path)

        assert result == "test-org/test-repo"

    def test_get_repo_name_https(self, tmp_path: Path) -> None:
        """Test getting repo name from HTTPS URL."""
        from bridge.handlers.secrets import SecretsHandler

        handler = SecretsHandler()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="https://github.com/test-org/test-repo.git\n",
            )
            result = handler._get_repo_name(tmp_path)

        assert result == "test-org/test-repo"

    def test_get_repo_name_not_git(self, tmp_path: Path) -> None:
        """Test getting repo name from non-git directory."""
        from bridge.handlers.secrets import SecretsHandler

        handler = SecretsHandler()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            result = handler._get_repo_name(tmp_path)

        assert result is None
