"""Supabase CLI executor for migrations."""

from rich.console import Console

from devflow.core.config import DevflowConfig
from devflow.migrations.executors.base import ExecutionResult, MigrationExecutor
from devflow.providers.supabase import SupabaseProvider

console = Console()


class SupabaseCLIExecutor(MigrationExecutor):
    """Execute migrations using Supabase CLI.

    This executor:
    - Uses `supabase db push --db-url` for applying migrations
    - Relies on Supabase CLI's built-in migration tracking
    - Works with self-hosted Supabase (no cloud project required)
    - Supports dry-run mode
    """

    def __init__(self, config: DevflowConfig, environment: str):
        """Initialize Supabase CLI executor.

        Args:
            config: Devflow configuration
            environment: Target environment
        """
        super().__init__(config, environment)
        self.provider = SupabaseProvider()

    @property
    def name(self) -> str:
        return "supabase"

    def apply(self, ci_mode: bool = False) -> ExecutionResult:
        """Apply migrations using Supabase CLI.

        Uses `supabase db push --db-url` to apply pending migrations.
        Supabase CLI handles its own migration tracking in
        supabase_migrations.schema_migrations.

        Args:
            ci_mode: If True, running in CI environment

        Returns:
            ExecutionResult with success status and counts
        """
        result = ExecutionResult(success=True)

        if not self.provider.is_available():
            result.success = False
            result.error = "Supabase CLI not installed. Run: npm install -g supabase"
            return result

        db_url = self.get_db_url()
        if not db_url:
            result.success = False
            result.error = f"No database URL configured for {self.environment}"
            return result

        if not self.migrations_dir.exists():
            result.success = False
            result.error = f"Migrations directory not found: {self.migrations_dir}"
            return result

        console.print("[dim]Using Supabase CLI for migrations...[/dim]")

        # Apply migrations
        push_result = self.provider.db_push(
            db_url=db_url,
            migrations_dir=str(self.migrations_dir),
        )

        if push_result.success:
            result.success = True
            result.applied = push_result.applied_count
            result.details["message"] = push_result.message

            if push_result.applied_count > 0:
                console.print(f"[green]Applied {push_result.applied_count} migration(s)[/green]")
            else:
                console.print("[green]No pending migrations.[/green]")
        else:
            result.success = False
            result.error = push_result.error or push_result.message
            console.print(f"[red]Migration failed: {result.error}[/red]")

        return result

    def get_pending(self) -> list[str]:
        """Get list of pending migrations.

        Uses Supabase CLI's dry-run mode to determine pending migrations.
        """
        db_url = self.get_db_url()
        if not db_url:
            return []

        if not self.provider.is_available():
            return []

        # Use dry-run to check pending
        self.provider.db_push(
            db_url=db_url,
            migrations_dir=str(self.migrations_dir),
            dry_run=True,
        )

        # Supabase CLI dry-run doesn't provide individual migration names
        # We fall back to comparing local files vs what we can determine
        local = set(self.get_local_migrations())
        applied = set(self.get_applied())

        return sorted(local - applied)

    def get_applied(self) -> list[str]:
        """Get list of applied migrations.

        Queries the Supabase migrations tracking table directly.
        """
        db_url = self.get_db_url()
        if not db_url:
            return []

        try:
            import psycopg2

            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()

            # Supabase CLI uses supabase_migrations.schema_migrations
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'supabase_migrations'
                    AND table_name = 'schema_migrations'
                )
                """
            )
            exists = cursor.fetchone()[0]

            if not exists:
                conn.close()
                return []

            cursor.execute(
                """
                SELECT version FROM supabase_migrations.schema_migrations
                ORDER BY version
                """
            )
            # Supabase stores version as timestamp, we need to match to filenames
            versions = [row[0] for row in cursor.fetchall()]
            conn.close()

            # Map versions back to filenames
            local_files = self.get_local_migrations()
            applied = []
            for filename in local_files:
                # Extract timestamp from filename (e.g., 20240101000000_initial.sql)
                timestamp = filename.split("_")[0]
                if timestamp in versions:
                    applied.append(filename)

            return applied

        except ImportError:
            console.print("[yellow]psycopg2 not installed, cannot check applied migrations[/yellow]")
            return []
        except Exception as e:
            console.print(f"[yellow]Could not query applied migrations: {e}[/yellow]")
            return []

    def diff(self, migration_name: str | None = None) -> tuple[bool, str]:
        """Generate schema diff.

        Args:
            migration_name: Optional name for generated migration file

        Returns:
            Tuple of (has_changes, diff_sql)
        """
        db_url = self.get_db_url()
        if not db_url:
            return False, "No database URL configured"

        if not self.provider.is_available():
            return False, "Supabase CLI not available"

        diff_result = self.provider.db_diff(
            db_url=db_url,
            migrations_dir=str(self.migrations_dir),
            migration_name=migration_name,
        )

        if diff_result.error:
            return False, diff_result.error

        return diff_result.has_changes, diff_result.diff_sql

    def gen_types(self, output_path: str = "src/types/supabase.ts") -> tuple[bool, str]:
        """Generate TypeScript types from database schema.

        Args:
            output_path: Output file path

        Returns:
            Tuple of (success, error_message)
        """
        db_url = self.get_db_url()
        if not db_url:
            return False, "No database URL configured"

        if not self.provider.is_available():
            return False, "Supabase CLI not available"

        return self.provider.gen_types(db_url, output_path)

    def reset(self, confirm: bool = False) -> ExecutionResult:
        """Reset database (DANGEROUS - drops all data).

        Args:
            confirm: Must be True to execute

        Returns:
            ExecutionResult
        """
        result = ExecutionResult(success=True)

        if not confirm:
            result.success = False
            result.error = "Reset requires explicit confirmation (confirm=True)"
            return result

        # Check production BEFORE checking db_url
        if self.environment == "production":
            result.success = False
            result.error = "Cannot reset production database"
            return result

        db_url = self.get_db_url()
        if not db_url:
            result.success = False
            result.error = "No database URL configured"
            return result

        success, error = self.provider.db_reset(db_url)
        result.success = success
        result.error = error

        return result
