#!/usr/bin/env python3
"""DevFlow UI Bridge Server - Entry point."""

import logging
import sys

from .handlers import (
    AgentsHandler,
    AIHandler,
    CodeHandler,
    ComponentsHandler,
    ConfigHandler,
    ContextHandler,
    DatabaseHandler,
    DeployHandler,
    DevHandler,
    DocsHandler,
    DomainsHandler,
    InfraHandler,
    LogsHandler,
    ProjectsHandler,
    SecretsHandler,
    SetupHandler,
    SystemHandler,
    TemplatesHandler,
    ToolsHandler,
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
    server.register_handler(SetupHandler(), "setup")
    server.register_handler(ConfigHandler(), "config")
    server.register_handler(ProjectsHandler(), "projects")
    server.register_handler(InfraHandler(), "infra")
    server.register_handler(ContextHandler(), "context")
    server.register_handler(DatabaseHandler(), "db")
    server.register_handler(DeployHandler(), "deploy")
    server.register_handler(SecretsHandler(), "secrets")
    server.register_handler(DevHandler(), "dev")
    server.register_handler(TemplatesHandler(), "templates")
    server.register_handler(ToolsHandler(), "tools")
    server.register_handler(DomainsHandler(), "domains")
    server.register_handler(LogsHandler(), "logs")
    server.register_handler(AgentsHandler(), "agents")
    server.register_handler(DocsHandler(), "docs")
    server.register_handler(ComponentsHandler(), "components")
    server.register_handler(CodeHandler(), "code")
    server.register_handler(AIHandler(), "ai")

    logger.info("All handlers registered")

    # Run server
    try:
        server.run()
    except Exception as e:
        logger.exception(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
