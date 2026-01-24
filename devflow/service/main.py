"""DevFlow service entry point.

Runs DevFlow as a TCP service for remote/WSL2 communication.

Usage:
    python -m devflow.service.main [--host HOST] [--port PORT]

    # Or via the CLI:
    devflow service start [--port PORT]
"""

import argparse
import asyncio
import logging
import signal
import sys
from typing import Optional

from devflow.service.server import DevFlowServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def register_all_handlers(server: DevFlowServer) -> None:
    """Register all available handlers with the server.

    Args:
        server: The DevFlowServer instance to register handlers with.
    """
    # Import handlers here to avoid circular imports
    from bridge.handlers.config import ConfigHandler
    from bridge.handlers.database import DatabaseHandler
    from bridge.handlers.deploy import DeployHandler
    from bridge.handlers.dev import DevHandler
    from bridge.handlers.infra import InfraHandler
    from bridge.handlers.projects import ProjectsHandler
    from bridge.handlers.secrets import SecretsHandler
    from bridge.handlers.system import SystemHandler

    # Register all handlers with their prefixes
    server.register_handler(SystemHandler(), "system")
    server.register_handler(DevHandler(), "dev")
    server.register_handler(DatabaseHandler(), "database")
    server.register_handler(DeployHandler(), "deploy")
    server.register_handler(SecretsHandler(), "secrets")
    server.register_handler(ConfigHandler(), "config")
    server.register_handler(InfraHandler(), "infra")
    server.register_handler(ProjectsHandler(), "projects")

    logger.info("All handlers registered")


def run_server(host: str = "127.0.0.1", port: int = 9876) -> None:
    """Run the DevFlow server synchronously.

    Args:
        host: Host address to bind to.
        port: Port number to listen on.
    """
    server = DevFlowServer(host=host, port=port)
    register_all_handlers(server)

    # Set up signal handlers for graceful shutdown
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def shutdown_handler(sig: signal.Signals, frame: Optional[object]) -> None:
        logger.info(f"Received signal {sig.name}, shutting down...")
        server.stop()
        loop.stop()

    # Register signal handlers
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        loop.run_until_complete(server.start())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        server.stop()
        loop.close()


async def run_server_async(host: str = "127.0.0.1", port: int = 9876) -> DevFlowServer:
    """Run the DevFlow server asynchronously.

    Args:
        host: Host address to bind to.
        port: Port number to listen on.

    Returns:
        The running DevFlowServer instance.
    """
    server = DevFlowServer(host=host, port=port)
    register_all_handlers(server)
    await server.start_background()
    return server


def main() -> None:
    """Main entry point for the service."""
    parser = argparse.ArgumentParser(description="DevFlow TCP service for remote/WSL2 communication")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind to (default: 127.0.0.1, use 0.0.0.0 for all interfaces)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9876,
        help="Port number to listen on (default: 9876)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info(f"Starting DevFlow service on {args.host}:{args.port}")
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
