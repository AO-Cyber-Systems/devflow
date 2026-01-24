"""Pytest configuration and fixtures."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio

from devflow.core.platform import Platform


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_dir: Path) -> Path:
    """Create a mock devflow.yml configuration."""
    config_content = """
version: "1"

project:
  name: test-project

database:
  migrations:
    directory: supabase/migrations
    format: sql
    tracking_table: schema_migrations

  environments:
    local:
      url_env: DATABASE_URL
    staging:
      url_secret: test_database_url
      host: test-host
      ssh_user: deploy

secrets:
  provider: 1password
  vault: Test

deployment:
  registry: ghcr.io
  organization: test-org

development:
  compose_file: docker-compose.yml
"""
    config_path = temp_dir / "devflow.yml"
    config_path.write_text(config_content)

    # Change to temp directory for tests
    original_dir = os.getcwd()
    os.chdir(temp_dir)

    yield config_path

    os.chdir(original_dir)


@pytest.fixture
def migrations_dir(temp_dir: Path) -> Path:
    """Create a mock migrations directory."""
    migrations = temp_dir / "supabase" / "migrations"
    migrations.mkdir(parents=True)

    # Create some test migration files
    (migrations / "20240101000000_initial.sql").write_text("CREATE TABLE users (id SERIAL PRIMARY KEY);")
    (migrations / "20240102000000_add_email.sql").write_text("ALTER TABLE users ADD COLUMN email TEXT;")
    (migrations / "20240103000000_add_index.sql").write_text("CREATE INDEX idx_users_email ON users(email);")

    return migrations


# =============================================================================
# Platform Mocking Fixtures
# =============================================================================


@pytest.fixture
def mock_linux():
    """Mock Linux platform for testing."""
    with patch("devflow.core.platform.CURRENT_PLATFORM", Platform.LINUX):
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.LINUX):
            yield Platform.LINUX


@pytest.fixture
def mock_macos():
    """Mock macOS platform for testing."""
    with patch("devflow.core.platform.CURRENT_PLATFORM", Platform.MACOS):
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.MACOS):
            yield Platform.MACOS


@pytest.fixture
def mock_windows():
    """Mock Windows platform for testing."""
    with patch("devflow.core.platform.CURRENT_PLATFORM", Platform.WINDOWS):
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WINDOWS):
            yield Platform.WINDOWS


@pytest.fixture
def mock_wsl2():
    """Mock WSL2 platform for testing."""
    with patch("devflow.core.platform.CURRENT_PLATFORM", Platform.WSL2):
        with patch("devflow.core.paths.CURRENT_PLATFORM", Platform.WSL2):
            yield Platform.WSL2


# =============================================================================
# TCP Server Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def tcp_server():
    """Create a test TCP server on a random port."""
    from devflow.service.server import DevFlowServer

    server = DevFlowServer(host="127.0.0.1", port=0)
    await server.start_background()
    yield server
    server.stop()


@pytest_asyncio.fixture
async def tcp_client(tcp_server):
    """Create a connected TCP client to the test server."""
    import asyncio

    host, port = tcp_server.get_address()
    reader, writer = await asyncio.open_connection(host, port)
    yield (reader, writer)
    writer.close()
    await writer.wait_closed()
