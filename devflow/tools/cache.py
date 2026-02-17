"""Cache management for tool browser data."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def get_cache_dir() -> Path:
    """Get the cache directory for tool browser data."""
    cache_dir = Path.home() / ".devflow" / "cache" / "tools"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cache_path(name: str) -> Path:
    """Get the path to a cache file."""
    return get_cache_dir() / f"{name}.json"


def is_cache_valid(name: str, max_age: timedelta) -> bool:
    """Check if a cache file exists and is not expired.

    Args:
        name: Cache file name (without .json extension)
        max_age: Maximum age of the cache before it's considered stale

    Returns:
        True if cache exists and is valid, False otherwise.
    """
    cache_path = get_cache_path(name)

    if not cache_path.exists():
        return False

    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    age = datetime.now() - mtime

    return age < max_age


def load_cache(name: str) -> Any | None:
    """Load data from a cache file.

    Args:
        name: Cache file name (without .json extension)

    Returns:
        Cached data or None if cache doesn't exist.
    """
    cache_path = get_cache_path(name)

    if not cache_path.exists():
        return None

    try:
        with open(cache_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load cache {name}: {e}")
        return None


def save_cache(name: str, data: Any) -> None:
    """Save data to a cache file.

    Args:
        name: Cache file name (without .json extension)
        data: Data to cache (must be JSON serializable)
    """
    cache_path = get_cache_path(name)

    try:
        with open(cache_path, "w") as f:
            json.dump(data, f)
        logger.debug(f"Saved cache {name}")
    except (TypeError, OSError) as e:
        logger.warning(f"Failed to save cache {name}: {e}")


def clear_cache(name: str | None = None) -> None:
    """Clear cache file(s).

    Args:
        name: Specific cache to clear, or None to clear all.
    """
    if name:
        cache_path = get_cache_path(name)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Cleared cache {name}")
    else:
        cache_dir = get_cache_dir()
        for cache_file in cache_dir.glob("*.json"):
            cache_file.unlink()
            logger.debug(f"Cleared cache {cache_file.name}")


def get_cache_info() -> dict[str, Any]:
    """Get information about cached data.

    Returns:
        Dictionary with cache status for each file.
    """
    cache_dir = get_cache_dir()
    info = {}

    for cache_file in cache_dir.glob("*.json"):
        name = cache_file.stem
        stat = cache_file.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        age = datetime.now() - mtime

        info[name] = {
            "exists": True,
            "size_bytes": stat.st_size,
            "modified": mtime.isoformat(),
            "age_hours": round(age.total_seconds() / 3600, 1),
        }

    return info
