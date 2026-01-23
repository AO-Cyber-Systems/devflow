#!/usr/bin/env python3
"""DevFlow UI Bridge Server - Entry point."""

import logging
import sys

from .handlers import (
    ConfigHandler,
    DatabaseHandler,
    DeployHandler,
    DevHandler,
    InfraHandler,
    ProjectsHandler,
    SecretsHandler,
    SystemHandler,
)
from .server import RpcServer


def setup_logging() -> None:
    """Configure logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,  # Log to stderr so stdout is clean for RPC
    )


def main() -> None:
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting DevFlow UI Bridge Server")

    # Create server
    server = RpcServer()

    # Register handlers
    server.register_handler(SystemHandler(), "system")
    server.register_handler(ConfigHandler(), "config")
    server.register_handler(ProjectsHandler(), "projects")
    server.register_handler(InfraHandler(), "infra")
    server.register_handler(DatabaseHandler(), "db")
    server.register_handler(DeployHandler(), "deploy")
    server.register_handler(SecretsHandler(), "secrets")
    server.register_handler(DevHandler(), "dev")

    logger.info("All handlers registered")

    # Run server
    try:
        server.run()
    except Exception as e:
        logger.exception(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
