"""Migration execution engine."""

import time
from pathlib import Path
from typing import Any, Optional

from rich.console import Console

from devflow.core.config import DevflowConfig
from devflow.core.errors import MigrationError
from devflow.migrations.tracker import MigrationTracker

console = Console()


class MigrationEngine:
    """Execute database migrations with proper locking."""

    def __init__(self, config: DevflowConfig, environment: str):
        """Initialize migration engine."""
        self.config = config
        self.environment = environment
        self.tracker = MigrationTracker(config, environment)
        self.migrations_dir = Path(config.database.migrations.directory)

    def get_pending_migrations(self) -> list[str]:
        """Get list of pending migrations."""
        return self.tracker.get_pending_migrations()

    def apply_migrations(self, ci_mode: bool = False) -> dict[str, Any]:
        """
        Apply all pending migrations.

        Returns:
            dict with keys: success, applied, skipped, error
        """
        result = {
            "success": True,
            "applied": 0,
            "skipped": 0,
            "error": None,
        }

        pending = self.get_pending_migrations()
        if not pending:
            console.print("[green]No pending migrations.[/green]")
            return result

        # Get database connection
        db_url = self.config.get_database_url(self.environment)
        if not db_url:
            result["success"] = False
            result["error"] = f"No database URL configured for {self.environment}"
            return result

        try:
            import psycopg2

            conn = psycopg2.connect(db_url)
        except ImportError:
            result["success"] = False
            result["error"] = "psycopg2 not installed"
            return result
        except Exception as e:
            result["success"] = False
            result["error"] = f"Database connection failed: {e}"
            return result

        try:
            # Ensure tracking table exists
            self.tracker.ensure_tracking_table(conn)

            # Acquire migration lock
            from devflow.core.locking import migration_lock

            project_name = self.config.project.name

            with migration_lock(conn, project_name):
                console.print(f"[dim]Acquired migration lock for {project_name}[/dim]")

                for migration_name in pending:
                    migration_path = self.migrations_dir / migration_name

                    if not migration_path.exists():
                        console.print(f"[yellow]Skipping {migration_name}: file not found[/yellow]")
                        result["skipped"] += 1
                        continue

                    # Compute checksum
                    checksum = MigrationTracker.compute_checksum(migration_path)

                    # Execute migration
                    console.print(f"Applying: [bold]{migration_name}[/bold]...")
                    start_time = time.time()

                    try:
                        sql = migration_path.read_text()
                        cursor = conn.cursor()
                        cursor.execute(sql)
                        conn.commit()

                        execution_time_ms = int((time.time() - start_time) * 1000)

                        # Record success
                        self.tracker.record_migration(
                            connection=conn,
                            name=migration_name,
                            checksum=checksum,
                            execution_time_ms=execution_time_ms,
                            success=True,
                            applied_from="ci" if ci_mode else "cli",
                        )

                        result["applied"] += 1
                        console.print(f"  [green]Applied in {execution_time_ms}ms[/green]")

                    except Exception as e:
                        conn.rollback()
                        result["success"] = False
                        result["error"] = f"Migration {migration_name} failed: {e}"

                        # Record failure
                        self.tracker.record_migration(
                            connection=conn,
                            name=migration_name,
                            checksum=checksum,
                            execution_time_ms=0,
                            success=False,
                            applied_from="ci" if ci_mode else "cli",
                        )

                        console.print(f"  [red]Failed: {e}[/red]")
                        return result

        finally:
            conn.close()

        return result

    def validate_migration(self, filepath: Path) -> list[str]:
        """Validate a migration file before execution."""
        errors = []

        if not filepath.exists():
            errors.append(f"File not found: {filepath}")
            return errors

        content = filepath.read_text()

        # Basic SQL validation
        if not content.strip():
            errors.append("Migration file is empty")

        # Check for dangerous operations in non-reversible migrations
        dangerous_keywords = ["DROP TABLE", "TRUNCATE", "DELETE FROM"]
        for keyword in dangerous_keywords:
            if keyword in content.upper():
                errors.append(f"Warning: Migration contains '{keyword}' (ensure this is intentional)")

        return errors
