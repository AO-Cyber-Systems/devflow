"""Tests for database bridge handler."""

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestDatabaseHandlerStatus:
    """Tests for DatabaseHandler.status()."""

    def test_status_no_config(self, tmp_path: Path) -> None:
        """Test status when no devflow.yml exists."""
        from bridge.handlers.database import DatabaseHandler

        handler = DatabaseHandler()
        result = handler.status(str(tmp_path), "local")

        assert "error" in result
        assert "devflow.yml" in result["error"]

    @patch("bridge.handlers.database.load_project_config")
    def test_status_no_database_config(self, mock_load: MagicMock) -> None:
        """Test status when no database section in config."""
        from bridge.handlers.database import DatabaseHandler

        mock_config = MagicMock()
        mock_config.database = None
        mock_load.return_value = mock_config

        handler = DatabaseHandler()
        result = handler.status("/some/path", "local")

        assert "error" in result
        assert "database" in result["error"].lower()

    @patch("bridge.handlers.database.load_project_config")
    def test_status_migrations_dir_not_exists(self, mock_load: MagicMock, tmp_path: Path) -> None:
        """Test status when migrations directory doesn't exist."""
        from bridge.handlers.database import DatabaseHandler

        mock_config = MagicMock()
        mock_config.database.migrations.directory = "migrations"
        mock_config.database.migrations.format = "sql"
        mock_load.return_value = mock_config

        handler = DatabaseHandler()
        result = handler.status(str(tmp_path), "local")

        assert result["migrations_dir_exists"] is False
        assert result["total"] == 0

    @patch("bridge.handlers.database.MigrationEngine")
    @patch("bridge.handlers.database.load_project_config")
    def test_status_success(self, mock_load: MagicMock, mock_engine_class: MagicMock, tmp_path: Path) -> None:
        """Test successful status retrieval."""
        from bridge.handlers.database import DatabaseHandler

        # Create migrations dir
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()
        (migrations_dir / "001_init.sql").write_text("CREATE TABLE test;")

        mock_config = MagicMock()
        mock_config.database.migrations.directory = "migrations"
        mock_config.database.migrations.format = "sql"
        mock_load.return_value = mock_config

        mock_engine = MagicMock()
        mock_engine.get_status.return_value = {
            "total": 3,
            "applied": 2,
            "pending": 1,
            "pending_files": ["003_pending.sql"],
            "applied_files": ["001_init.sql", "002_update.sql"],
            "executor": "sql",
        }
        mock_engine_class.return_value = mock_engine

        handler = DatabaseHandler()
        result = handler.status(str(tmp_path), "local")

        assert result["applied"] == 2
        assert result["pending"] == 1
        assert result["total"] == 3
        assert result["migrations_dir_exists"] is True


class TestDatabaseHandlerMigrate:
    """Tests for DatabaseHandler.migrate()."""

    @patch("bridge.handlers.database.MigrationEngine")
    @patch("bridge.handlers.database.load_project_config")
    def test_migrate_dry_run(self, mock_load: MagicMock, mock_engine_class: MagicMock, tmp_path: Path) -> None:
        """Test migrate with dry_run flag."""
        from bridge.handlers.database import DatabaseHandler

        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        mock_config = MagicMock()
        mock_config.database.migrations.directory = "migrations"
        mock_config.database.environments = {"local": MagicMock()}
        mock_load.return_value = mock_config

        mock_engine = MagicMock()
        mock_engine.get_pending_migrations.return_value = ["001_init.sql", "002_update.sql"]
        mock_engine_class.return_value = mock_engine

        handler = DatabaseHandler()
        result = handler.migrate(str(tmp_path), "local", dry_run=True)

        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["would_apply"] == 2

    @patch("bridge.handlers.database.MigrationEngine")
    @patch("bridge.handlers.database.load_project_config")
    def test_migrate_success(self, mock_load: MagicMock, mock_engine_class: MagicMock, tmp_path: Path) -> None:
        """Test successful migration."""
        from bridge.handlers.database import DatabaseHandler

        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        mock_config = MagicMock()
        mock_config.database.migrations.directory = "migrations"
        mock_config.database.environments = {"local": MagicMock()}
        mock_load.return_value = mock_config

        mock_engine = MagicMock()
        mock_engine.get_pending_migrations.return_value = ["001_init.sql"]
        mock_engine.apply_migrations.return_value = {
            "success": True,
            "applied": 1,
            "skipped": 0,
            "error": None,
        }
        mock_engine_class.return_value = mock_engine

        handler = DatabaseHandler()
        result = handler.migrate(str(tmp_path), "local")

        assert result["success"] is True
        assert result["applied"] == 1
        mock_engine.apply_migrations.assert_called_once_with(ci_mode=True)

    @patch("bridge.handlers.database.load_project_config")
    def test_migrate_environment_not_found(self, mock_load: MagicMock, tmp_path: Path) -> None:
        """Test migrate when environment doesn't exist."""
        from bridge.handlers.database import DatabaseHandler

        mock_config = MagicMock()
        mock_config.database.environments = {}
        mock_load.return_value = mock_config

        handler = DatabaseHandler()
        result = handler.migrate(str(tmp_path), "unknown")

        assert result["success"] is False
        assert "unknown" in result["error"]


class TestDatabaseHandlerRollback:
    """Tests for DatabaseHandler.rollback()."""

    @patch("bridge.handlers.database.SQLExecutor")
    @patch("bridge.handlers.database.load_project_config")
    def test_rollback_dry_run(self, mock_load: MagicMock, mock_executor_class: MagicMock) -> None:
        """Test rollback with dry_run flag."""
        from bridge.handlers.database import DatabaseHandler

        mock_config = MagicMock()
        mock_config.database.environments = {"local": MagicMock()}
        mock_load.return_value = mock_config

        mock_executor = MagicMock()
        mock_executor.get_db_url.return_value = "postgresql://localhost/test"
        mock_executor.get_applied_with_connection.return_value = [
            "001_init.sql",
            "002_update.sql",
        ]
        mock_executor_class.return_value = mock_executor

        handler = DatabaseHandler()
        result = handler.rollback("/some/path", "local", steps=1, dry_run=True)

        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["would_rollback"] == 1
        assert "002_update.sql" in result["migrations"]

    @patch("bridge.handlers.database.SQLExecutor")
    @patch("bridge.handlers.database.load_project_config")
    def test_rollback_success(self, mock_load: MagicMock, mock_executor_class: MagicMock) -> None:
        """Test successful rollback."""
        from bridge.handlers.database import DatabaseHandler

        mock_config = MagicMock()
        mock_config.database.environments = {"local": MagicMock()}
        mock_load.return_value = mock_config

        mock_result = MagicMock()
        mock_result.success = True

        mock_executor = MagicMock()
        mock_executor.get_db_url.return_value = "postgresql://localhost/test"
        mock_executor.get_applied_with_connection.return_value = ["001_init.sql"]
        mock_executor.rollback_migration.return_value = mock_result
        mock_executor_class.return_value = mock_executor

        handler = DatabaseHandler()
        result = handler.rollback("/some/path", "local", steps=1)

        assert result["success"] is True
        assert result["rolled_back"] == 1


class TestDatabaseHandlerCreate:
    """Tests for DatabaseHandler.create()."""

    @patch("bridge.handlers.database.load_project_config")
    def test_create_migration(self, mock_load: MagicMock, tmp_path: Path) -> None:
        """Test creating a new migration file."""
        from bridge.handlers.database import DatabaseHandler

        mock_config = MagicMock()
        mock_config.database.migrations.directory = "migrations"
        mock_load.return_value = mock_config

        handler = DatabaseHandler()
        result = handler.create(str(tmp_path), "add users table")

        assert result["success"] is True
        assert "add_users_table.sql" in result["file"]
        assert (tmp_path / "migrations" / result["file"]).exists()


class TestDatabaseHandlerTestConnection:
    """Tests for DatabaseHandler.test_connection()."""

    @patch("bridge.handlers.database.load_project_config")
    def test_connection_no_url(self, mock_load: MagicMock) -> None:
        """Test connection when no URL configured."""
        from bridge.handlers.database import DatabaseHandler

        mock_config = MagicMock()
        mock_config.database.environments = {"local": MagicMock(url_env="DATABASE_URL")}
        mock_config.get_database_url.return_value = None
        mock_load.return_value = mock_config

        handler = DatabaseHandler()
        result = handler.test_connection("/some/path", "local")

        assert result["success"] is False
        assert "DATABASE_URL" in result["error"]

    @patch("psycopg2.connect")
    @patch("bridge.handlers.database.load_project_config")
    def test_connection_success(self, mock_load: MagicMock, mock_connect: MagicMock) -> None:
        """Test successful connection."""
        from bridge.handlers.database import DatabaseHandler

        mock_config = MagicMock()
        mock_config.database.environments = {"local": MagicMock()}
        mock_config.get_database_url.return_value = "postgresql://localhost/test"
        mock_load.return_value = mock_config

        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            ("PostgreSQL 15.0",),  # version
            ("testdb",),  # database name
            ("testuser",),  # user
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        handler = DatabaseHandler()
        result = handler.test_connection("/some/path", "local")

        assert result["success"] is True
        assert result["database"] == "testdb"
        assert result["user"] == "testuser"
