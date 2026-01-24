"""JSON-RPC 2.0 server for DevFlow UI bridge."""

import json
import logging
import sys
from typing import Any, Callable

from .types import ErrorCodes, RpcError, RpcRequest, RpcResponse

logger = logging.getLogger(__name__)


class RpcServer:
    """JSON-RPC 2.0 server that communicates over stdin/stdout."""

    def __init__(self) -> None:
        self._methods: dict[str, Callable[..., Any]] = {}
        self._running = False

    def register_method(self, name: str, handler: Callable[..., Any]) -> None:
        """Register an RPC method handler."""
        self._methods[name] = handler
        logger.debug(f"Registered method: {name}")

    def register_handler(self, handler: object, prefix: str = "") -> None:
        """Register all methods from a handler class."""
        for name in dir(handler):
            if name.startswith("_"):
                continue
            method = getattr(handler, name)
            if callable(method):
                method_name = f"{prefix}.{name}" if prefix else name
                self.register_method(method_name, method)

    def _parse_request(self, line: str) -> RpcRequest | RpcResponse:
        """Parse a JSON-RPC request from a line of input."""
        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            return RpcResponse(
                error=RpcError(ErrorCodes.PARSE_ERROR, f"Parse error: {e}"),
            )

        # Validate required fields
        if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
            return RpcResponse(
                error=RpcError(ErrorCodes.INVALID_REQUEST, "Invalid JSON-RPC version"),
            )

        if "method" not in data:
            return RpcResponse(
                error=RpcError(ErrorCodes.INVALID_REQUEST, "Missing method"),
            )

        if "id" not in data:
            return RpcResponse(
                error=RpcError(ErrorCodes.INVALID_REQUEST, "Missing id"),
            )

        return RpcRequest(
            jsonrpc=data["jsonrpc"],
            method=data["method"],
            id=data["id"],
            params=data.get("params"),
        )

    def _execute_method(self, request: RpcRequest) -> RpcResponse:
        """Execute an RPC method and return the response."""
        if request.method not in self._methods:
            return RpcResponse(
                id=request.id,
                error=RpcError(ErrorCodes.METHOD_NOT_FOUND, f"Method not found: {request.method}"),
            )

        handler = self._methods[request.method]

        try:
            # Call the handler with params
            if request.params is None:
                result = handler()
            elif isinstance(request.params, dict):
                result = handler(**request.params)
            elif isinstance(request.params, list):
                result = handler(*request.params)
            else:
                result = handler(request.params)

            return RpcResponse(id=request.id, result=result)

        except TypeError as e:
            return RpcResponse(
                id=request.id,
                error=RpcError(ErrorCodes.INVALID_PARAMS, f"Invalid params: {e}"),
            )
        except Exception as e:
            logger.exception(f"Error executing method {request.method}")
            return RpcResponse(
                id=request.id,
                error=RpcError(ErrorCodes.INTERNAL_ERROR, str(e)),
            )

    def handle_request(self, line: str) -> str:
        """Handle a single request line and return the response JSON."""
        parsed = self._parse_request(line)

        if isinstance(parsed, RpcResponse):
            # Parse error
            response = parsed
        else:
            # Valid request, execute it
            response = self._execute_method(parsed)

        return json.dumps(response.to_dict())

    def run(self) -> None:
        """Run the server, reading from stdin and writing to stdout."""
        self._running = True
        logger.info("Bridge server started")

        while self._running:
            try:
                line = sys.stdin.readline()
                if not line:
                    # EOF - stdin closed
                    logger.info("EOF received, shutting down")
                    break

                line = line.strip()
                if not line:
                    continue

                logger.debug(f"Received: {line}")

                response = self.handle_request(line)

                logger.debug(f"Sending: {response}")
                print(response, flush=True)

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt, shutting down")
                break
            except Exception as e:
                logger.exception("Unexpected error in main loop")
                # Send error response
                error_response = RpcResponse(
                    error=RpcError(ErrorCodes.INTERNAL_ERROR, f"Server error: {e}"),
                )
                print(json.dumps(error_response.to_dict()), flush=True)

        self._running = False
        logger.info("Bridge server stopped")

    def stop(self) -> None:
        """Stop the server."""
        self._running = False
