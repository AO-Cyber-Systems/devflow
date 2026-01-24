"""TCP JSON-RPC server for remote DevFlow communication.

This server enables Windows Tauri apps to communicate with the Python
backend running in WSL2 via TCP instead of stdio.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class DevFlowServer:
    """TCP server for DevFlow JSON-RPC communication.

    Provides a JSON-RPC 2.0 interface over TCP for remote clients.
    Designed to run as a daemon/service in WSL2 for Windows integration.
    """

    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 9876

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        """Initialize the DevFlow server.

        Args:
            host: Host address to bind to. Use "0.0.0.0" for all interfaces.
            port: Port number to listen on.
        """
        self.host = host
        self.port = port
        self.handlers: Dict[str, Callable[..., Any]] = {}
        self._server: Optional[asyncio.AbstractServer] = None
        self._running = False

    def register_handler(self, handler: object, prefix: str = "") -> None:
        """Register handler methods for RPC calls.

        Scans the handler object for public methods (not starting with _)
        and registers them as RPC methods.

        Args:
            handler: Object with methods to register as handlers.
            prefix: Optional prefix for method names (e.g., "system" -> "system.ping").
        """
        for name in dir(handler):
            if name.startswith("_"):
                continue
            method = getattr(handler, name)
            if callable(method):
                full_name = f"{prefix}.{name}" if prefix else name
                self.handlers[full_name] = method
                logger.debug(f"Registered handler: {full_name}")

    def register_method(self, name: str, method: Callable[..., Any]) -> None:
        """Register a single method as an RPC handler.

        Args:
            name: The RPC method name.
            method: The callable to invoke.
        """
        self.handlers[name] = method
        logger.debug(f"Registered handler: {name}")

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle an incoming client connection.

        Reads JSON-RPC requests line by line and sends responses.

        Args:
            reader: Stream reader for the client connection.
            writer: Stream writer for the client connection.
        """
        addr = writer.get_extra_info("peername")
        logger.info(f"Client connected: {addr}")

        try:
            while self._running:
                # Read a line (JSON-RPC request)
                data = await reader.readline()
                if not data:
                    break

                try:
                    request_str = data.decode().strip()
                    if not request_str:
                        continue

                    logger.debug(f"Received: {request_str}")
                    request = json.loads(request_str)
                    response = await self._process_request(request)

                    response_str = json.dumps(response) + "\n"
                    writer.write(response_str.encode())
                    await writer.drain()
                    logger.debug(f"Sent: {response_str.strip()}")

                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": f"Parse error: {e}"},
                        "id": None,
                    }
                    writer.write((json.dumps(error_response) + "\n").encode())
                    await writer.drain()

        except asyncio.CancelledError:
            logger.debug(f"Client handler cancelled: {addr}")
        except ConnectionResetError:
            logger.debug(f"Connection reset by client: {addr}")
        except Exception as e:
            logger.exception(f"Error handling client {addr}: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            logger.info(f"Client disconnected: {addr}")

    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a JSON-RPC request and return a response.

        Args:
            request: The parsed JSON-RPC request dictionary.

        Returns:
            JSON-RPC response dictionary.
        """
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")

        # Validate JSON-RPC version
        if request.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "Invalid Request: jsonrpc must be '2.0'"},
                "id": request_id,
            }

        # Check if method exists
        if method not in self.handlers:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": request_id,
            }

        try:
            handler = self.handlers[method]

            # Handle params as dict or positional args
            if isinstance(params, dict):
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(**params) if params else await handler()
                else:
                    result = handler(**params) if params else handler()
            elif isinstance(params, list):
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(*params) if params else await handler()
                else:
                    result = handler(*params) if params else handler()
            else:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler()
                else:
                    result = handler()

            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id,
            }

        except TypeError as e:
            # Likely a parameter mismatch
            logger.warning(f"Parameter error for {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": f"Invalid params: {e}"},
                "id": request_id,
            }
        except Exception as e:
            logger.exception(f"Error handling {method}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)},
                "id": request_id,
            }

    async def start(self) -> None:
        """Start the TCP server.

        Blocks until the server is stopped or cancelled.
        """
        self._running = True
        self._server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )

        # Get actual port if 0 was specified
        if self.port == 0:
            addrs = self._server.sockets[0].getsockname()
            self.port = addrs[1]

        logger.info(f"DevFlow server listening on {self.host}:{self.port}")

        async with self._server:
            await self._server.serve_forever()

    async def start_background(self) -> None:
        """Start the server in background mode.

        Returns immediately after starting. Use stop() to shut down.
        """
        self._running = True
        self._server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )

        # Get actual port if 0 was specified
        if self.port == 0:
            addrs = self._server.sockets[0].getsockname()
            self.port = addrs[1]

        logger.info(f"DevFlow server listening on {self.host}:{self.port}")
        asyncio.create_task(self._server.serve_forever())

    def stop(self) -> None:
        """Stop the server."""
        self._running = False
        if self._server:
            self._server.close()
            logger.info("DevFlow server stopped")

    @property
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running and self._server is not None

    def get_address(self) -> tuple[str, int]:
        """Get the server's bound address.

        Returns:
            Tuple of (host, port).
        """
        return (self.host, self.port)
