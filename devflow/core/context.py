"""Execution context for devflow operations."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from devflow.core.config import DevflowConfig, load_project_config


@dataclass
class ExecutionContext:
    """Context for executing devflow commands."""

    # Environment
    environment: str = "local"
    is_ci: bool = False
    verbose: bool = False
    dry_run: bool = False

    # Project info
    project_root: Path = field(default_factory=Path.cwd)
    config: DevflowConfig | None = None

    # Runtime state
    user: str = field(default_factory=lambda: os.environ.get("USER", "unknown"))
    ci_run_id: str | None = None

    @classmethod
    def from_environment(cls) -> "ExecutionContext":
        """Create context from current environment."""
        ctx = cls()

        # Detect environment
        ctx.environment = os.environ.get("DEVFLOW_ENV", "local")

        # Detect CI
        ctx.is_ci = any(
            [
                os.environ.get("CI"),
                os.environ.get("GITHUB_ACTIONS"),
                os.environ.get("GITLAB_CI"),
                os.environ.get("JENKINS_URL"),
            ]
        )

        # Get CI run ID if available
        ctx.ci_run_id = os.environ.get("GITHUB_RUN_ID") or os.environ.get("CI_JOB_ID")

        # Load config
        ctx.config = load_project_config()
        if ctx.config:
            # Find project root from config location
            from devflow.core.config import find_config_file

            config_path = find_config_file()
            if config_path:
                ctx.project_root = config_path.parent

        return ctx

    @property
    def project_name(self) -> str:
        """Get project name from config or directory."""
        if self.config:
            return self.config.project.name
        return self.project_root.name

    @property
    def migrations_dir(self) -> Path:
        """Get absolute path to migrations directory."""
        if self.config:
            return self.project_root / self.config.database.migrations.directory
        return self.project_root / "supabase" / "migrations"

    def get_database_url(self) -> str | None:
        """Get database URL for current environment."""
        if not self.config:
            return os.environ.get("DATABASE_URL")
        return self.config.get_database_url(self.environment)


# Global context instance
_context: ExecutionContext | None = None


def get_context() -> ExecutionContext:
    """Get the current execution context."""
    global _context
    if _context is None:
        _context = ExecutionContext.from_environment()
    return _context


def set_context(ctx: ExecutionContext) -> None:
    """Set the execution context (mainly for testing)."""
    global _context
    _context = ctx
