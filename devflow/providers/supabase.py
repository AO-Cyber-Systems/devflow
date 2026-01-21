"""Supabase CLI provider for self-hosted deployments."""

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from devflow.providers.base import Provider


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    success: bool
    applied_count: int
    message: str
    error: Optional[str] = None


@dataclass
class DiffResult:
    """Result of a schema diff operation."""

    has_changes: bool
    diff_sql: str
    error: Optional[str] = None


class SupabaseProvider(Provider):
    """Wrapper for Supabase CLI.

    For self-hosted Supabase, we cannot use `supabase link` as it requires
    a Supabase Cloud project reference. Instead, we use --db-url flag
    for all database operations.
    """

    @property
    def name(self) -> str:
        return "supabase"

    @property
    def binary(self) -> str:
        return "supabase"

    def is_available(self) -> bool:
        """Check if Supabase CLI is installed."""
        return shutil.which(self.binary) is not None

    def is_authenticated(self) -> bool:
        """For self-hosted deployments, authentication is not required.

        The Supabase CLI uses --db-url directly for all operations,
        bypassing the need for `supabase link` or cloud authentication.
        """
        return self.is_available()

    def db_push(
        self,
        db_url: str,
        migrations_dir: str = "supabase/migrations",
        dry_run: bool = False,
    ) -> MigrationResult:
        """Apply migrations using Supabase CLI.

        Uses `supabase db push --db-url` to apply all pending migrations
        to a self-hosted database.

        Args:
            db_url: PostgreSQL connection URL
            migrations_dir: Path to migrations directory
            dry_run: If True, show what would be applied without executing

        Returns:
            MigrationResult with success status and details
        """
        if not self.is_available():
            return MigrationResult(
                success=False,
                applied_count=0,
                message="Supabase CLI not installed",
                error="supabase binary not found in PATH",
            )

        args = ["db", "push", "--db-url", db_url]

        if dry_run:
            args.append("--dry-run")

        # Set the project directory context if migrations aren't in default location
        migrations_path = Path(migrations_dir)
        if migrations_path.exists():
            # Supabase CLI expects migrations in supabase/migrations by default
            # If the config specifies a different directory, we need to handle it
            # For now, assume standard Supabase structure
            pass

        try:
            result = subprocess.run(
                [self.binary] + args,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for migrations
            )

            if result.returncode == 0:
                # Parse output to count applied migrations
                output = result.stdout
                # Supabase CLI outputs "Applied migration ..." for each
                applied_count = output.count("Applied migration")

                if applied_count == 0 and "No migrations" in output:
                    return MigrationResult(
                        success=True,
                        applied_count=0,
                        message="No pending migrations",
                    )

                return MigrationResult(
                    success=True,
                    applied_count=applied_count,
                    message=f"Applied {applied_count} migration(s)",
                )
            else:
                return MigrationResult(
                    success=False,
                    applied_count=0,
                    message="Migration failed",
                    error=result.stderr or result.stdout,
                )

        except subprocess.TimeoutExpired:
            return MigrationResult(
                success=False,
                applied_count=0,
                message="Migration timed out",
                error="Operation exceeded 5 minute timeout",
            )
        except subprocess.SubprocessError as e:
            return MigrationResult(
                success=False,
                applied_count=0,
                message="Migration error",
                error=str(e),
            )

    def db_diff(
        self,
        db_url: str,
        migrations_dir: str = "supabase/migrations",
        migration_name: Optional[str] = None,
    ) -> DiffResult:
        """Generate schema diff between local migrations and remote database.

        Uses `supabase db diff --db-url` to compare the current database state
        with the expected schema from migrations.

        Args:
            db_url: PostgreSQL connection URL
            migrations_dir: Path to migrations directory
            migration_name: Optional name for the generated migration

        Returns:
            DiffResult with diff SQL and change status
        """
        if not self.is_available():
            return DiffResult(
                has_changes=False,
                diff_sql="",
                error="supabase binary not found in PATH",
            )

        args = ["db", "diff", "--db-url", db_url]

        if migration_name:
            args.extend(["--file", migration_name])

        try:
            result = subprocess.run(
                [self.binary] + args,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                diff_sql = result.stdout.strip()
                has_changes = bool(diff_sql and diff_sql != "-- No changes")

                return DiffResult(
                    has_changes=has_changes,
                    diff_sql=diff_sql,
                )
            else:
                return DiffResult(
                    has_changes=False,
                    diff_sql="",
                    error=result.stderr or result.stdout,
                )

        except subprocess.TimeoutExpired:
            return DiffResult(
                has_changes=False,
                diff_sql="",
                error="Diff operation timed out",
            )
        except subprocess.SubprocessError as e:
            return DiffResult(
                has_changes=False,
                diff_sql="",
                error=str(e),
            )

    def gen_types(
        self,
        db_url: str,
        output_path: str = "src/types/supabase.ts",
        schema: str = "public",
    ) -> tuple[bool, str]:
        """Generate TypeScript types from database schema.

        Uses `supabase gen types typescript` to create type definitions.

        Args:
            db_url: PostgreSQL connection URL
            output_path: Output file path for generated types
            schema: Database schema to generate types for

        Returns:
            Tuple of (success, error_message)
        """
        if not self.is_available():
            return False, "supabase binary not found in PATH"

        args = [
            "gen",
            "types",
            "typescript",
            "--db-url",
            db_url,
            "--schema",
            schema,
        ]

        try:
            result = subprocess.run(
                [self.binary] + args,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Write output to file
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(result.stdout)
                return True, ""
            else:
                return False, result.stderr or result.stdout

        except subprocess.TimeoutExpired:
            return False, "Type generation timed out"
        except subprocess.SubprocessError as e:
            return False, str(e)

    def db_reset(self, db_url: str) -> tuple[bool, str]:
        """Reset database to clean state (DANGEROUS).

        This drops all data and reapplies migrations. Only use in development.

        Args:
            db_url: PostgreSQL connection URL

        Returns:
            Tuple of (success, error_message)
        """
        if not self.is_available():
            return False, "supabase binary not found in PATH"

        args = ["db", "reset", "--db-url", db_url]

        try:
            result = subprocess.run(
                [self.binary] + args,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                return True, ""
            else:
                return False, result.stderr or result.stdout

        except subprocess.TimeoutExpired:
            return False, "Reset operation timed out"
        except subprocess.SubprocessError as e:
            return False, str(e)

    def db_lint(self, migrations_dir: str = "supabase/migrations") -> tuple[bool, list[str]]:
        """Lint migrations for potential issues.

        Args:
            migrations_dir: Path to migrations directory

        Returns:
            Tuple of (success, list of warnings/errors)
        """
        if not self.is_available():
            return False, ["supabase binary not found in PATH"]

        args = ["db", "lint"]

        try:
            result = subprocess.run(
                [self.binary] + args,
                capture_output=True,
                text=True,
                timeout=60,
            )

            warnings = []
            if result.stdout:
                warnings = [
                    line.strip()
                    for line in result.stdout.split("\n")
                    if line.strip()
                ]

            return result.returncode == 0, warnings

        except subprocess.TimeoutExpired:
            return False, ["Lint operation timed out"]
        except subprocess.SubprocessError as e:
            return False, [str(e)]

    def get_migration_status(self, db_url: str) -> dict:
        """Get status of migrations against remote database.

        Args:
            db_url: PostgreSQL connection URL

        Returns:
            Dict with applied, pending, and total counts
        """
        if not self.is_available():
            return {
                "error": "supabase binary not found in PATH",
                "applied": 0,
                "pending": 0,
                "total": 0,
            }

        # Supabase CLI tracks migrations in supabase_migrations.schema_migrations
        # We can query this or use db push --dry-run to see pending
        args = ["db", "push", "--db-url", db_url, "--dry-run"]

        try:
            result = subprocess.run(
                [self.binary] + args,
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Parse dry-run output to determine status
            output = result.stdout
            pending_count = output.count("Would apply migration")

            return {
                "pending": pending_count,
                "applied": 0,  # Would need separate query
                "total": pending_count,  # Incomplete without applied count
            }

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return {
                "error": "Failed to get migration status",
                "applied": 0,
                "pending": 0,
                "total": 0,
            }
