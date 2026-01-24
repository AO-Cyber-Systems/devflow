"""Type definitions for the bridge server."""

from dataclasses import dataclass
from typing import Any


@dataclass
class RpcRequest:
    """JSON-RPC 2.0 request."""

    jsonrpc: str
    method: str
    id: int | str
    params: dict[str, Any] | list[Any] | None = None


@dataclass
class RpcError:
    """JSON-RPC 2.0 error object."""

    code: int
    message: str
    data: Any | None = None


@dataclass
class RpcResponse:
    """JSON-RPC 2.0 response."""

    jsonrpc: str = "2.0"
    result: Any | None = None
    error: RpcError | None = None
    id: int | str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        response: dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            response["error"] = {
                "code": self.error.code,
                "message": self.error.message,
            }
            if self.error.data is not None:
                response["error"]["data"] = self.error.data
        else:
            response["result"] = self.result
        return response


# Standard JSON-RPC error codes
class ErrorCodes:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # Custom error codes (server-defined)
    CONFIG_ERROR = -32000
    PROJECT_ERROR = -32001
    INFRA_ERROR = -32002
    DATABASE_ERROR = -32003
    DEPLOY_ERROR = -32004
    SECRETS_ERROR = -32005
    DEV_ERROR = -32006
    SYSTEM_ERROR = -32007


@dataclass
class OperationResult:
    """Standard result wrapper for operations."""

    success: bool
    message: str = ""
    data: Any | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {"success": self.success}
        if self.message:
            result["message"] = self.message
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        return result
