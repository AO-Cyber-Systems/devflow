"""Base migration executor interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from devflow.core.config import DevflowConfig


@dataclass
class ExecutionResult:
    """Result of migration execution."""

    success: bool
    applied: int = 0
    skipped: int = 0
    error: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "applied": self.applied,
            "skipped": self.skipped,
            "error": self.error,
            "details": self.details,
        }


class MigrationExecutor(ABC):
    """Abstract base class for migration executors.

    Different backends (raw SQL, Supabase CLI, Prisma, etc.) implement
    this interface to provide consistent migration functionality.
    """

    def __init__(self, config: DevflowConfig, environment: str):
        """Initialize executor with configuration.

        Args:
            config: Devflow configuration
            environment: Target environment (local, staging, production)
        """
        self.config = config
        self.environment = environment
        self.migrations_dir = Path(config.database.migrations.directory)

    @property
    @abstractmethod
    def name(self) -> str:
        """Executor name for identification."""
        pass

    @abstractmethod
    def apply(self, ci_mode: bool = False) -> ExecutionResult:
        """Apply all pending migrations.

        Args:
            ci_mode: If True, running in CI environment (non-interactive)

        Returns:
            ExecutionResult with success status and counts
        """
        pass

    @abstractmethod
    def get_pending(self) -> list[str]:
        """Get list of pending migration names.

        Returns:
            List of migration filenames that haven't been applied
        """
        pass

    @abstractmethod
    def get_applied(self) -> list[str]:
        """Get list of applied migration names.

        Returns:
            List of migration filenames that have been applied
        """
        pass

    def get_local_migrations(self) -> list[str]:
        """Get list of local migration files.

        Returns:
            Sorted list of migration filenames
        """
        if not self.migrations_dir.exists():
            return []

        files = sorted(self.migrations_dir.glob("*.sql"))
        return [f.name for f in files]

    def get_db_url(self) -> Optional[str]:
        """Get database URL for current environment.

        Returns:
            Database URL string or None if not configured
        """
        return self.config.get_database_url(self.environment)

    def validate_environment(self) -> tuple[bool, Optional[str]]:
        """Validate that the environment is properly configured.

        Returns:
            Tuple of (is_valid, error_message)
        """
        db_url = self.get_db_url()
        if not db_url:
            return False, f"No database URL configured for environment '{self.environment}'"

        if not self.migrations_dir.exists():
            return False, f"Migrations directory not found: {self.migrations_dir}"

        return True, None
