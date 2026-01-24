"""Database RPC handlers."""

from datetime import datetime
from pathlib import Path
from typing import Any

from devflow.core.config import load_project_config
from devflow.migrations.engine import MigrationEngine
from devflow.migrations.executors.sql import SQLExecutor


class DatabaseHandler:
    """Handler for database RPC methods."""

    def status(self, path: str, environment: str = "local") -> dict[str, Any]:
        """Get migration status.

        Args:
            path: Project path
            environment: Target environment

        Returns:
            Dict with applied, pending, total counts and file lists
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"error": "No devflow.yml configuration found"}

            if not config.database:
                return {"error": "No database configuration found"}

            migrations_dir = project_path / config.database.migrations.directory
            if not migrations_dir.exists():
                return {
                    "environment": environment,
                    "executor": config.database.migrations.format,
                    "applied": 0,
                    "pending": 0,
                    "total": 0,
                    "pending_files": [],
                    "applied_files": [],
                    "migrations_dir_exists": False,
                }

            # Use MigrationEngine to get real status
            engine = MigrationEngine(config, environment)
            status_data = engine.get_status()

            return {
                "environment": environment,
                "executor": status_data.get("executor", config.database.migrations.format),
                "applied": status_data["applied"],
                "pending": status_data["pending"],
                "total": status_data["total"],
                "pending_files": status_data["pending_files"],
                "applied_files": status_data.get("applied_files", []),
                "migrations_dir_exists": True,
            }
        except Exception as e:
            return {"error": str(e)}

    def migrate(
        self, path: str, environment: str = "local", dry_run: bool = False
    ) -> dict[str, Any]:
        """Run pending migrations.

        Args:
            path: Project path
            environment: Target environment
            dry_run: If True, only show what would be applied

        Returns:
            Dict with success status, applied count, and results
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.database:
                return {"success": False, "error": "No database configuration found"}

            # Get environment config
            env_config = config.database.environments.get(environment)
            if not env_config:
                return {
                    "success": False,
                    "error": f"Environment not found: {environment}",
                }

            migrations_dir = project_path / config.database.migrations.directory
            if not migrations_dir.exists():
                return {"success": False, "error": "Migrations directory not found"}

            # Use MigrationEngine
            engine = MigrationEngine(config, environment)
            pending = engine.get_pending_migrations()

            if dry_run:
                return {
                    "success": True,
                    "dry_run": True,
                    "would_apply": len(pending),
                    "files": pending,
                }

            if not pending:
                return {
                    "success": True,
                    "applied": 0,
                    "skipped": 0,
                    "message": "No pending migrations",
                }

            # Apply migrations (ci_mode=True for non-interactive RPC context)
            result = engine.apply_migrations(ci_mode=True)

            return {
                "success": result["success"],
                "applied": result["applied"],
                "skipped": result["skipped"],
                "error": result.get("error"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def rollback(
        self,
        path: str,
        environment: str = "local",
        steps: int = 1,
        dry_run: bool = False,
        force: bool = False,
    ) -> dict[str, Any]:
        """Rollback migrations.

        Args:
            path: Project path
            environment: Target environment
            steps: Number of migrations to rollback
            dry_run: If True, only show what would be rolled back
            force: Force rollback even without .down.sql files

        Returns:
            Dict with success status and rollback results
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.database:
                return {"success": False, "error": "No database configuration found"}

            # Get environment config
            env_config = config.database.environments.get(environment)
            if not env_config:
                return {
                    "success": False,
                    "error": f"Environment not found: {environment}",
                }

            # Use SQLExecutor for rollback
            executor = SQLExecutor(config, environment)
            db_url = executor.get_db_url()

            if not db_url:
                return {
                    "success": False,
                    "error": f"No database URL configured for {environment}",
                }

            # Get applied migrations (most recent first)
            applied = executor.get_applied_with_connection(db_url)
            if not applied:
                return {
                    "success": False,
                    "error": "No applied migrations to rollback",
                }

            # Get migrations to rollback (most recent N)
            to_rollback = list(reversed(applied))[:steps]

            if dry_run:
                return {
                    "success": True,
                    "dry_run": True,
                    "would_rollback": len(to_rollback),
                    "migrations": to_rollback,
                }

            # Rollback each migration
            results = []
            rolled_back = 0
            failed = 0

            for migration_name in to_rollback:
                result = executor.rollback_migration(migration_name)
                if result.success:
                    rolled_back += 1
                    results.append({
                        "migration": migration_name,
                        "status": "rolled_back",
                        "error": None,
                    })
                else:
                    failed += 1
                    results.append({
                        "migration": migration_name,
                        "status": "failed",
                        "error": result.error,
                    })
                    # Stop on first failure unless force is set
                    if not force:
                        break

            return {
                "success": failed == 0,
                "rolled_back": rolled_back,
                "failed": failed,
                "results": results,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create(self, path: str, name: str) -> dict[str, Any]:
        """Create a new migration.

        Args:
            path: Project path
            name: Migration name

        Returns:
            Dict with success status and created file path
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.database:
                return {"success": False, "error": "No database configuration found"}

            migrations_dir = project_path / config.database.migrations.directory
            migrations_dir.mkdir(parents=True, exist_ok=True)

            # Generate migration filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            safe_name = name.lower().replace(" ", "_").replace("-", "_")
            filename = f"{timestamp}_{safe_name}.sql"

            migration_path = migrations_dir / filename

            # Create migration file with template
            template = f"""-- Migration: {name}
-- Created: {datetime.now().isoformat()}

-- Write your migration SQL here

-- UP migration

-- DOWN migration (rollback)
"""
            migration_path.write_text(template)

            return {"success": True, "file": filename, "path": str(migration_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def history(
        self, path: str, environment: str = "local", limit: int | None = None
    ) -> dict[str, Any]:
        """Get migration history from the database.

        Args:
            path: Project path
            environment: Target environment
            limit: Maximum number of records to return

        Returns:
            Dict with migration history records
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"error": "No devflow.yml configuration found"}

            if not config.database:
                return {"error": "No database configuration found"}

            # Get database URL
            db_url = config.get_database_url(environment)
            if not db_url:
                return {"error": f"No database URL configured for {environment}"}

            # Query the tracking table directly
            try:
                import psycopg2

                conn = psycopg2.connect(db_url)
                cursor = conn.cursor()

                schema = config.database.migrations.tracking_schema
                table = config.database.migrations.tracking_table

                # Check if tracking table exists
                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = %s
                    )
                    """,
                    (schema, table),
                )
                exists = cursor.fetchone()[0]

                if not exists:
                    conn.close()
                    return {
                        "environment": environment,
                        "history": [],
                        "total": 0,
                        "message": "No migrations have been applied yet",
                    }

                # Build query
                query = f"""
                    SELECT name, checksum, applied_at, execution_time_ms,
                           success, applied_by, applied_from, rolled_back_at
                    FROM {schema}.{table}
                    ORDER BY applied_at DESC
                """
                if limit:
                    query += f" LIMIT {int(limit)}"

                cursor.execute(query)
                rows = cursor.fetchall()

                history = []
                for row in rows:
                    history.append({
                        "name": row[0],
                        "checksum": row[1],
                        "applied_at": row[2].isoformat() if row[2] else None,
                        "execution_time_ms": row[3],
                        "success": row[4],
                        "applied_by": row[5],
                        "applied_from": row[6],
                        "rolled_back_at": row[7].isoformat() if row[7] else None,
                    })

                conn.close()

                return {
                    "environment": environment,
                    "history": history,
                    "total": len(history),
                }

            except ImportError:
                return {"error": "psycopg2 not installed. Run: pip install psycopg2-binary"}

        except Exception as e:
            return {"error": str(e)}

    def test_connection(self, path: str, environment: str = "local") -> dict[str, Any]:
        """Test database connection.

        Args:
            path: Project path
            environment: Target environment

        Returns:
            Dict with connection status and database info
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.database:
                return {"success": False, "error": "No database configuration found"}

            env_config = config.database.environments.get(environment)
            if not env_config:
                return {
                    "success": False,
                    "error": f"Environment not found: {environment}",
                }

            # Get database URL
            db_url = config.get_database_url(environment)
            if not db_url:
                return {
                    "success": False,
                    "error": f"No database URL configured for {environment}. "
                    f"Set the {env_config.url_env or 'DATABASE_URL'} environment variable.",
                }

            # Test connection
            try:
                import psycopg2

                conn = psycopg2.connect(db_url, connect_timeout=10)
                cursor = conn.cursor()

                # Get PostgreSQL version
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]

                # Get current database name
                cursor.execute("SELECT current_database()")
                database = cursor.fetchone()[0]

                # Get current user
                cursor.execute("SELECT current_user")
                user = cursor.fetchone()[0]

                conn.close()

                return {
                    "success": True,
                    "environment": environment,
                    "database": database,
                    "user": user,
                    "version": version,
                }

            except ImportError:
                return {
                    "success": False,
                    "error": "psycopg2 not installed. Run: pip install psycopg2-binary",
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Connection failed: {e}",
                }

        except Exception as e:
            return {"success": False, "error": str(e)}
