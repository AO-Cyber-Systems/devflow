"""Migration execution engine."""

from pathlib import Path
from typing import Any, Optional

from rich.console import Console

from devflow.core.config import DevflowConfig
from devflow.core.errors import MigrationError
from devflow.migrations.executors.base import ExecutionResult, MigrationExecutor
from devflow.migrations.tracker import MigrationTracker

console = Console()


class MigrationEngine:
    """Execute database migrations using pluggable executors.

    The engine selects an appropriate executor based on the configured
    migration format:
    - 'sql': Direct SQL execution with psycopg2 and advisory locking
    - 'supabase': Supabase CLI with `supabase db push --db-url`
    """

    def __init__(self, config: DevflowConfig, environment: str):
        """Initialize migration engine.

        Args:
            config: Devflow configuration
            environment: Target environment (local, staging, production)
        """
        self.config = config
        self.environment = environment
        self.tracker = MigrationTracker(config, environment)
        self.migrations_dir = Path(config.database.migrations.directory)
        self._executor: Optional[MigrationExecutor] = None

    def _get_executor(self) -> MigrationExecutor:
        """Get the appropriate migration executor based on configuration.

        Returns:
            MigrationExecutor instance for the configured format
        """
        if self._executor is not None:
            return self._executor

        # Check configuration for executor type
        format_type = self.config.database.migrations.format.lower()
        use_supabase_cli = getattr(self.config.database.migrations, "use_supabase_cli", False)

        if format_type == "supabase" or use_supabase_cli:
            from devflow.migrations.executors.supabase_cli import SupabaseCLIExecutor

            self._executor = SupabaseCLIExecutor(self.config, self.environment)
            console.print(f"[dim]Using Supabase CLI executor[/dim]")
        else:
            # Default to SQL executor (supports 'sql' and legacy configs)
            from devflow.migrations.executors.sql import SQLExecutor

            self._executor = SQLExecutor(self.config, self.environment)

        return self._executor

    def get_pending_migrations(self) -> list[str]:
        """Get list of pending migrations.

        Returns:
            List of pending migration filenames
        """
        executor = self._get_executor()
        return executor.get_pending()

    def apply_migrations(self, ci_mode: bool = False) -> dict[str, Any]:
        """Apply all pending migrations.

        Delegates to the configured executor.

        Args:
            ci_mode: If True, running in CI environment (non-interactive)

        Returns:
            dict with keys: success, applied, skipped, error
        """
        executor = self._get_executor()
        result = executor.apply(ci_mode=ci_mode)

        # Convert ExecutionResult to dict for backwards compatibility
        return {
            "success": result.success,
            "applied": result.applied,
            "skipped": result.skipped,
            "error": result.error,
        }

    def get_status(self) -> dict[str, Any]:
        """Get migration status summary.

        Returns:
            Dict with total, applied, pending counts and file lists
        """
        executor = self._get_executor()

        local = executor.get_local_migrations()
        applied = executor.get_applied()
        pending = executor.get_pending()

        return {
            "total": len(local),
            "applied": len(applied),
            "pending": len(pending),
            "local_files": local,
            "applied_files": applied,
            "pending_files": pending,
            "executor": executor.name,
        }

    def set_executor(self, executor: MigrationExecutor) -> None:
        """Explicitly set the migration executor.

        Useful for testing or forcing a specific executor.

        Args:
            executor: MigrationExecutor instance to use
        """
        self._executor = executor

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
