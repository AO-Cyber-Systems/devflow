"""Distributed locking using PostgreSQL advisory locks."""

from __future__ import annotations

import hashlib
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from devflow.core.errors import LockError

if TYPE_CHECKING:
    import psycopg2.extensions


def get_lock_id(name: str) -> int:
    """Convert a lock name to a PostgreSQL advisory lock ID."""
    # Use first 8 bytes of MD5 hash as a 64-bit integer
    hash_bytes = hashlib.md5(name.encode()).digest()[:8]
    return int.from_bytes(hash_bytes, byteorder="big", signed=True)


class AdvisoryLock:
    """PostgreSQL advisory lock manager."""

    def __init__(self, connection: psycopg2.extensions.connection, lock_name: str):
        """
        Initialize advisory lock.

        Args:
            connection: PostgreSQL database connection
            lock_name: Unique name for this lock
        """
        self.connection = connection
        self.lock_name = lock_name
        self.lock_id = get_lock_id(lock_name)
        self._acquired = False

    def acquire(self, timeout_seconds: int = 30) -> bool:
        """
        Attempt to acquire the advisory lock.

        Args:
            timeout_seconds: How long to wait for lock

        Returns:
            True if lock was acquired, False if timeout

        Raises:
            LockError: If unable to acquire lock
        """
        if self._acquired:
            return True

        cursor = self.connection.cursor()
        try:
            # Set statement timeout
            cursor.execute(f"SET statement_timeout = '{timeout_seconds * 1000}ms'")

            # Try to acquire exclusive lock (pg_advisory_lock blocks until acquired)
            cursor.execute("SELECT pg_try_advisory_lock(%s)", (self.lock_id,))
            result = cursor.fetchone()

            if result and result[0]:
                self._acquired = True
                return True

            return False

        except Exception as e:
            raise LockError(f"Failed to acquire lock '{self.lock_name}': {e}")
        finally:
            # Reset timeout
            cursor.execute("SET statement_timeout = '0'")

    def release(self) -> None:
        """Release the advisory lock."""
        if not self._acquired:
            return

        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT pg_advisory_unlock(%s)", (self.lock_id,))
            self._acquired = False
        except Exception as e:
            raise LockError(f"Failed to release lock '{self.lock_name}': {e}")

    def is_locked(self) -> bool:
        """Check if the lock is currently held (by anyone)."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM pg_locks
            WHERE locktype = 'advisory' AND objid = %s
            """,
            (self.lock_id,),
        )
        result = cursor.fetchone()
        return result and result[0] > 0

    def __enter__(self) -> AdvisoryLock:
        """Context manager entry."""
        if not self.acquire():
            raise LockError(f"Could not acquire lock '{self.lock_name}'")
        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: object) -> None:
        """Context manager exit."""
        self.release()


@contextmanager
def migration_lock(
    connection: psycopg2.extensions.connection, project_name: str
) -> Generator[AdvisoryLock, None, None]:
    """
    Context manager for migration locking.

    Usage:
        with migration_lock(conn, "aocodex") as lock:
            # Run migrations here
            pass
    """
    lock_name = f"devflow_migrations_{project_name}"
    lock = AdvisoryLock(connection, lock_name)

    try:
        if not lock.acquire(timeout_seconds=60):
            raise LockError(
                f"Could not acquire migration lock for {project_name}. " "Another migration may be running."
            )
        yield lock
    finally:
        lock.release()
