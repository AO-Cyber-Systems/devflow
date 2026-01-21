"""Migration state tracking."""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from devflow.core.config import DevflowConfig


@dataclass
class MigrationRecord:
    """Record of an applied migration."""

    name: str
    checksum: str
    applied_at: datetime
    applied_by: str
    execution_time_ms: int
    success: bool
    devflow_version: str
    applied_from: str  # 'cli', 'ci', 'entrypoint'
    ci_run_id: Optional[str] = None


class MigrationTracker:
    """Track migration state in the database."""

    TRACKING_TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS {schema}.{table} (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        checksum VARCHAR(64) NOT NULL,
        applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        applied_by VARCHAR(255) DEFAULT CURRENT_USER,
        execution_time_ms INTEGER,
        success BOOLEAN DEFAULT TRUE,
        rolled_back_at TIMESTAMPTZ,
        notes TEXT,
        devflow_version VARCHAR(32),
        applied_from VARCHAR(64),
        ci_run_id VARCHAR(128)
    );

    CREATE INDEX IF NOT EXISTS ix_{table}_applied_at
        ON {schema}.{table}(applied_at);
    """

    def __init__(self, config: DevflowConfig, environment: str):
        """Initialize tracker with configuration."""
        self.config = config
        self.environment = environment
        self.table = config.database.migrations.tracking_table
        self.schema = config.database.migrations.tracking_schema
        self.migrations_dir = Path(config.database.migrations.directory)

    def get_local_migrations(self) -> list[str]:
        """Get list of migration files from the local directory."""
        if not self.migrations_dir.exists():
            return []

        # Get all SQL files, sorted by name
        files = sorted(self.migrations_dir.glob("*.sql"))
        return [f.name for f in files]

    def get_applied_migrations(self) -> list[str]:
        """Get list of applied migrations from database."""
        # Placeholder - will use actual database connection
        return []

    def get_pending_migrations(self) -> list[str]:
        """Get list of pending (not yet applied) migrations."""
        local = set(self.get_local_migrations())
        applied = set(self.get_applied_migrations())
        return sorted(local - applied)

    def get_status(self) -> dict:
        """Get migration status summary."""
        local = self.get_local_migrations()
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()

        return {
            "total": len(local),
            "applied": len(applied),
            "pending": len(pending),
            "local_files": local,
            "applied_files": applied,
            "pending_files": pending,
        }

    @staticmethod
    def compute_checksum(filepath: Path) -> str:
        """Compute SHA-256 checksum of a migration file."""
        content = filepath.read_bytes()
        return hashlib.sha256(content).hexdigest()

    def ensure_tracking_table(self, connection: "psycopg2.extensions.connection") -> None:
        """Ensure the migration tracking table exists."""
        ddl = self.TRACKING_TABLE_DDL.format(schema=self.schema, table=self.table)
        cursor = connection.cursor()
        cursor.execute(ddl)
        connection.commit()

    def record_migration(
        self,
        connection: "psycopg2.extensions.connection",
        name: str,
        checksum: str,
        execution_time_ms: int,
        success: bool,
        applied_from: str = "cli",
        ci_run_id: Optional[str] = None,
    ) -> None:
        """Record a migration as applied."""
        from devflow import __version__

        cursor = connection.cursor()
        cursor.execute(
            f"""
            INSERT INTO {self.schema}.{self.table}
                (name, checksum, execution_time_ms, success, devflow_version, applied_from, ci_run_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                checksum = EXCLUDED.checksum,
                applied_at = CURRENT_TIMESTAMP,
                execution_time_ms = EXCLUDED.execution_time_ms,
                success = EXCLUDED.success,
                devflow_version = EXCLUDED.devflow_version,
                applied_from = EXCLUDED.applied_from,
                ci_run_id = EXCLUDED.ci_run_id
            """,
            (name, checksum, execution_time_ms, success, __version__, applied_from, ci_run_id),
        )
        connection.commit()
