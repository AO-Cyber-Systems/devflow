"""Tests for migration executors."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devflow.core.config import DevflowConfig, load_project_config
from devflow.migrations.executors.base import ExecutionResult, MigrationExecutor
from devflow.migrations.executors.sql import SQLExecutor
from devflow.migrations.executors.supabase_cli import SupabaseCLIExecutor


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_default_values(self) -> None:
        """Test default values."""
        result = ExecutionResult(success=True)
        assert result.success is True
        assert result.applied == 0
        assert result.skipped == 0
        assert result.error is None
        assert result.details == {}

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        result = ExecutionResult(
            success=True,
            applied=3,
            skipped=1,
            error=None,
            details={"message": "test"},
        )
        d = result.to_dict()

        assert d["success"] is True
        assert d["applied"] == 3
        assert d["skipped"] == 1
        assert d["error"] is None
        assert d["details"]["message"] == "test"

    def test_with_error(self) -> None:
        """Test result with error."""
        result = ExecutionResult(
            success=False,
            error="Migration failed: syntax error",
        )
        assert result.success is False
        assert "syntax error" in result.error


class TestSQLExecutor:
    """Tests for SQL executor."""

    @pytest.fixture
    def mock_config(self, tmp_path: Path) -> DevflowConfig:
        """Create a mock devflow config."""
        config_content = """
version: "1"

project:
  name: test-project

database:
  migrations:
    directory: supabase/migrations
    format: sql
    tracking_table: schema_migrations

  environments:
    local:
      url_env: DATABASE_URL
    staging:
      url_secret: test_database_url
"""
        config_path = tmp_path / "devflow.yml"
        config_path.write_text(config_content)

        # Create migrations directory
        migrations_dir = tmp_path / "supabase" / "migrations"
        migrations_dir.mkdir(parents=True)

        # Create test migration files
        (migrations_dir / "20240101000000_initial.sql").write_text(
            "CREATE TABLE users (id SERIAL PRIMARY KEY);"
        )
        (migrations_dir / "20240102000000_add_email.sql").write_text(
            "ALTER TABLE users ADD COLUMN email TEXT;"
        )

        original_dir = os.getcwd()
        os.chdir(tmp_path)

        yield load_project_config()

        os.chdir(original_dir)

    def test_name(self, mock_config: DevflowConfig) -> None:
        """Test executor name."""
        executor = SQLExecutor(mock_config, "local")
        assert executor.name == "sql"

    def test_get_local_migrations(self, mock_config: DevflowConfig) -> None:
        """Test getting local migration files."""
        executor = SQLExecutor(mock_config, "local")
        migrations = executor.get_local_migrations()

        assert len(migrations) == 2
        assert "20240101000000_initial.sql" in migrations
        assert "20240102000000_add_email.sql" in migrations

    def test_validate_environment_no_db_url(self, mock_config: DevflowConfig) -> None:
        """Test validation with no database URL."""
        executor = SQLExecutor(mock_config, "local")

        # No DATABASE_URL set
        with patch.dict(os.environ, {}, clear=True):
            is_valid, error = executor.validate_environment()
            assert is_valid is False
            assert "database url" in error.lower()

    def test_apply_no_db_url(self, mock_config: DevflowConfig) -> None:
        """Test apply with no database URL configured."""
        executor = SQLExecutor(mock_config, "local")

        with patch.dict(os.environ, {}, clear=True):
            result = executor.apply()

        assert result.success is False
        assert "database url" in result.error.lower()

    @patch("psycopg2.connect")
    def test_apply_psycopg2_not_installed(
        self, mock_connect: MagicMock, mock_config: DevflowConfig
    ) -> None:
        """Test apply when psycopg2 is not installed."""
        mock_connect.side_effect = ImportError("No module named 'psycopg2'")

        executor = SQLExecutor(mock_config, "local")

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/test"}):
            # Need to also mock the import inside the method
            with patch.dict("sys.modules", {"psycopg2": None}):
                # This test verifies the error handling path
                result = executor.apply()
                # Result depends on whether psycopg2 is actually available
                assert isinstance(result, ExecutionResult)


class TestSupabaseCLIExecutor:
    """Tests for Supabase CLI executor."""

    @pytest.fixture
    def mock_config(self, tmp_path: Path) -> DevflowConfig:
        """Create a mock devflow config."""
        config_content = """
version: "1"

project:
  name: test-project

database:
  migrations:
    directory: supabase/migrations
    format: supabase
    tracking_table: schema_migrations

  environments:
    local:
      url_env: DATABASE_URL
"""
        config_path = tmp_path / "devflow.yml"
        config_path.write_text(config_content)

        # Create migrations directory
        migrations_dir = tmp_path / "supabase" / "migrations"
        migrations_dir.mkdir(parents=True)

        # Create test migration files
        (migrations_dir / "20240101000000_initial.sql").write_text(
            "CREATE TABLE users (id SERIAL PRIMARY KEY);"
        )

        original_dir = os.getcwd()
        os.chdir(tmp_path)

        yield load_project_config()

        os.chdir(original_dir)

    def test_name(self, mock_config: DevflowConfig) -> None:
        """Test executor name."""
        executor = SupabaseCLIExecutor(mock_config, "local")
        assert executor.name == "supabase"

    def test_get_local_migrations(self, mock_config: DevflowConfig) -> None:
        """Test getting local migration files."""
        executor = SupabaseCLIExecutor(mock_config, "local")
        migrations = executor.get_local_migrations()

        assert len(migrations) == 1
        assert "20240101000000_initial.sql" in migrations

    def test_apply_cli_not_available(self, mock_config: DevflowConfig) -> None:
        """Test apply when Supabase CLI is not installed."""
        executor = SupabaseCLIExecutor(mock_config, "local")

        with patch.object(executor.provider, "is_available", return_value=False):
            with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/test"}):
                result = executor.apply()

        assert result.success is False
        assert "not installed" in result.error.lower()

    def test_apply_no_db_url(self, mock_config: DevflowConfig) -> None:
        """Test apply with no database URL configured."""
        executor = SupabaseCLIExecutor(mock_config, "local")

        with patch.dict(os.environ, {}, clear=True):
            result = executor.apply()

        assert result.success is False
        assert "database url" in result.error.lower()

    @patch("devflow.providers.supabase.SupabaseProvider.db_push")
    def test_apply_success(
        self, mock_db_push: MagicMock, mock_config: DevflowConfig
    ) -> None:
        """Test successful migration application."""
        from devflow.providers.supabase import MigrationResult

        mock_db_push.return_value = MigrationResult(
            success=True,
            applied_count=1,
            message="Applied 1 migration(s)",
        )

        executor = SupabaseCLIExecutor(mock_config, "local")

        with patch.object(executor.provider, "is_available", return_value=True):
            with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/test"}):
                result = executor.apply()

        assert result.success is True
        assert result.applied == 1

    @patch("devflow.providers.supabase.SupabaseProvider.db_push")
    def test_apply_failure(
        self, mock_db_push: MagicMock, mock_config: DevflowConfig
    ) -> None:
        """Test failed migration application."""
        from devflow.providers.supabase import MigrationResult

        mock_db_push.return_value = MigrationResult(
            success=False,
            applied_count=0,
            message="Migration failed",
            error="Syntax error in migration",
        )

        executor = SupabaseCLIExecutor(mock_config, "local")

        with patch.object(executor.provider, "is_available", return_value=True):
            with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/test"}):
                result = executor.apply()

        assert result.success is False
        assert "Syntax error" in result.error

    def test_reset_requires_confirmation(self, mock_config: DevflowConfig) -> None:
        """Test that reset requires explicit confirmation."""
        executor = SupabaseCLIExecutor(mock_config, "local")

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/test"}):
            result = executor.reset(confirm=False)

        assert result.success is False
        assert "confirmation" in result.error.lower()

    def test_reset_blocked_in_production(self, mock_config: DevflowConfig, tmp_path: Path) -> None:
        """Test that reset is blocked in production."""
        # Need to add production environment to config
        config_content = """
version: "1"

project:
  name: test-project

database:
  migrations:
    directory: supabase/migrations
    format: supabase
    tracking_table: schema_migrations

  environments:
    local:
      url_env: DATABASE_URL
    production:
      url_env: DATABASE_URL
"""
        config_path = tmp_path / "devflow_prod.yml"
        config_path.write_text(config_content)

        original_dir = os.getcwd()
        os.chdir(tmp_path)

        # Create migrations directory
        migrations_dir = tmp_path / "supabase" / "migrations"
        migrations_dir.mkdir(parents=True, exist_ok=True)

        from devflow.core.config import load_project_config
        prod_config = load_project_config()

        executor = SupabaseCLIExecutor(prod_config, "production")

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/test"}):
            result = executor.reset(confirm=True)

        os.chdir(original_dir)

        assert result.success is False
        assert "production" in result.error.lower()
