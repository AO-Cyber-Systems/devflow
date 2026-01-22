"""SQL executor using psycopg2 with advisory locking."""

import time

from rich.console import Console

from devflow.core.config import DevflowConfig
from devflow.migrations.executors.base import ExecutionResult, MigrationExecutor
from devflow.migrations.tracker import MigrationTracker

console = Console()


class SQLExecutor(MigrationExecutor):
    """Execute raw SQL migrations with PostgreSQL advisory locking.

    This executor:
    - Uses psycopg2 for direct database connections
    - Implements PostgreSQL advisory locks for safe concurrent execution
    - Tracks migrations in a schema_migrations table
    - Computes checksums for migration integrity
    """

    def __init__(self, config: DevflowConfig, environment: str):
        """Initialize SQL executor.

        Args:
            config: Devflow configuration
            environment: Target environment
        """
        super().__init__(config, environment)
        self.tracker = MigrationTracker(config, environment)

    @property
    def name(self) -> str:
        return "sql"

    def apply(self, ci_mode: bool = False) -> ExecutionResult:
        """Apply all pending migrations with advisory locking.

        Args:
            ci_mode: If True, running in CI environment

        Returns:
            ExecutionResult with success status and counts
        """
        result = ExecutionResult(success=True)

        pending = self.get_pending()
        if not pending:
            console.print("[green]No pending migrations.[/green]")
            return result

        db_url = self.get_db_url()
        if not db_url:
            result.success = False
            result.error = f"No database URL configured for {self.environment}"
            return result

        try:
            import psycopg2
        except ImportError:
            result.success = False
            result.error = "psycopg2 not installed. Run: pip install psycopg2-binary"
            return result

        try:
            conn = psycopg2.connect(db_url)
        except Exception as e:
            result.success = False
            result.error = f"Database connection failed: {e}"
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
                        result.skipped += 1
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

                        result.applied += 1
                        console.print(f"  [green]Applied in {execution_time_ms}ms[/green]")

                    except Exception as e:
                        conn.rollback()
                        result.success = False
                        result.error = f"Migration {migration_name} failed: {e}"

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

    def get_pending(self) -> list[str]:
        """Get list of pending migrations.

        Compares local migration files against the tracking table.
        """
        return self.tracker.get_pending_migrations()

    def get_applied(self) -> list[str]:
        """Get list of applied migrations from tracking table."""
        return self.tracker.get_applied_migrations()

    def get_applied_with_connection(self, db_url: str) -> list[str]:
        """Get applied migrations using direct database connection.

        Args:
            db_url: Database connection URL

        Returns:
            List of applied migration names
        """
        try:
            import psycopg2

            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()

            # Check if tracking table exists
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = %s
                )
                """,
                (self.tracker.schema, self.tracker.table),
            )
            exists = cursor.fetchone()[0]

            if not exists:
                conn.close()
                return []

            cursor.execute(
                f"""
                SELECT name FROM {self.tracker.schema}.{self.tracker.table}
                WHERE success = TRUE
                ORDER BY applied_at
                """
            )
            applied = [row[0] for row in cursor.fetchall()]
            conn.close()
            return applied

        except Exception:
            return []

    def rollback_migration(self, migration_name: str, rollback_sql: str | None = None) -> ExecutionResult:
        """Rollback a specific migration.

        Note: Rollback requires either:
        - A corresponding .down.sql file
        - Explicit rollback SQL provided

        Args:
            migration_name: Name of migration to rollback
            rollback_sql: Optional explicit SQL to execute

        Returns:
            ExecutionResult
        """
        result = ExecutionResult(success=True)

        db_url = self.get_db_url()
        if not db_url:
            result.success = False
            result.error = f"No database URL configured for {self.environment}"
            return result

        # Find rollback SQL
        if not rollback_sql:
            # Look for .down.sql file
            down_file = self.migrations_dir / migration_name.replace(".sql", ".down.sql")
            if down_file.exists():
                rollback_sql = down_file.read_text()
            else:
                result.success = False
                result.error = f"No rollback SQL found for {migration_name}"
                return result

        try:
            import psycopg2

            conn = psycopg2.connect(db_url)

            from devflow.core.locking import migration_lock

            with migration_lock(conn, self.config.project.name):
                cursor = conn.cursor()
                cursor.execute(rollback_sql)

                # Mark as rolled back in tracking table
                cursor.execute(
                    f"""
                    UPDATE {self.tracker.schema}.{self.tracker.table}
                    SET rolled_back_at = CURRENT_TIMESTAMP
                    WHERE name = %s
                    """,
                    (migration_name,),
                )

                conn.commit()
                result.applied = 1
                console.print(f"[green]Rolled back: {migration_name}[/green]")

        except Exception as e:
            result.success = False
            result.error = f"Rollback failed: {e}"

        finally:
            if "conn" in locals():
                conn.close()

        return result
