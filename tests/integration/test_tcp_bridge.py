"""Integration tests for TCP bridge communication."""

import asyncio
import json
from typing import Any, Dict

import pytest
import pytest_asyncio

from devflow.service.server import DevFlowServer


class MockHandler:
    """Mock handler for testing."""

    def ping(self) -> Dict[str, Any]:
        """Simple ping method."""
        return {"pong": True}

    def echo(self, message: str) -> Dict[str, Any]:
        """Echo back the message."""
        return {"message": message}

    def add(self, a: int, b: int) -> Dict[str, Any]:
        """Add two numbers."""
        return {"result": a + b}

    def error(self) -> None:
        """Raise an error."""
        raise ValueError("Test error")


@pytest_asyncio.fixture
async def server():
    """Create and start a test server."""
    server = DevFlowServer(host="127.0.0.1", port=0)  # Random port
    server.register_handler(MockHandler(), "test")

    # Start server in background
    await server.start_background()
    yield server
    server.stop()


@pytest_asyncio.fixture
async def client_connection(server):
    """Create a client connection to the test server."""
    host, port = server.get_address()
    reader, writer = await asyncio.open_connection(host, port)
    yield (reader, writer)
    writer.close()
    await writer.wait_closed()


async def send_request(
    writer: asyncio.StreamWriter,
    reader: asyncio.StreamReader,
    method: str,
    params: Dict[str, Any] | None = None,
    request_id: int = 1,
) -> Dict[str, Any]:
    """Send a JSON-RPC request and get response."""
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": request_id,
    }

    request_str = json.dumps(request) + "\n"
    writer.write(request_str.encode())
    await writer.drain()

    response_line = await reader.readline()
    return json.loads(response_line.decode())


@pytest.mark.asyncio
async def test_server_starts_and_stops(server):
    """Test server can start and stop cleanly."""
    assert server.is_running
    host, port = server.get_address()
    assert host == "127.0.0.1"
    assert port > 0


@pytest.mark.asyncio
async def test_ping_handler(server, client_connection):
    """Test ping method returns pong."""
    reader, writer = client_connection

    response = await send_request(writer, reader, "test.ping")

    assert response.get("jsonrpc") == "2.0"
    assert response.get("id") == 1
    assert response.get("result") == {"pong": True}


@pytest.mark.asyncio
async def test_echo_handler(server, client_connection):
    """Test echo method returns the message."""
    reader, writer = client_connection

    response = await send_request(writer, reader, "test.echo", {"message": "Hello, World!"})

    assert response.get("result") == {"message": "Hello, World!"}


@pytest.mark.asyncio
async def test_add_handler(server, client_connection):
    """Test add method returns sum."""
    reader, writer = client_connection

    response = await send_request(writer, reader, "test.add", {"a": 5, "b": 3})

    assert response.get("result") == {"result": 8}


@pytest.mark.asyncio
async def test_method_not_found(server, client_connection):
    """Test unknown method returns error."""
    reader, writer = client_connection

    response = await send_request(writer, reader, "unknown.method")

    assert "error" in response
    assert response["error"]["code"] == -32601
    assert "Method not found" in response["error"]["message"]


@pytest.mark.asyncio
async def test_handler_error(server, client_connection):
    """Test handler error is returned properly."""
    reader, writer = client_connection

    response = await send_request(writer, reader, "test.error")

    assert "error" in response
    assert response["error"]["code"] == -32000
    assert "Test error" in response["error"]["message"]


@pytest.mark.asyncio
async def test_invalid_json(server, client_connection):
    """Test invalid JSON returns parse error."""
    reader, writer = client_connection

    writer.write(b"not valid json\n")
    await writer.drain()

    response_line = await reader.readline()
    response = json.loads(response_line.decode())

    assert "error" in response
    assert response["error"]["code"] == -32700


@pytest.mark.asyncio
async def test_invalid_jsonrpc_version(server, client_connection):
    """Test invalid JSON-RPC version returns error."""
    reader, writer = client_connection

    request = json.dumps({"jsonrpc": "1.0", "method": "test.ping", "id": 1}) + "\n"
    writer.write(request.encode())
    await writer.drain()

    response_line = await reader.readline()
    response = json.loads(response_line.decode())

    assert "error" in response
    assert response["error"]["code"] == -32600


@pytest.mark.asyncio
async def test_multiple_requests(server, client_connection):
    """Test multiple sequential requests."""
    reader, writer = client_connection

    for i in range(5):
        response = await send_request(writer, reader, "test.add", {"a": i, "b": i}, request_id=i)
        assert response.get("result") == {"result": i + i}
        assert response.get("id") == i


@pytest.mark.asyncio
async def test_register_method_directly():
    """Test registering a method directly."""
    server = DevFlowServer(host="127.0.0.1", port=0)

    def custom_method(x: int) -> Dict[str, int]:
        return {"squared": x * x}

    server.register_method("math.square", custom_method)

    assert "math.square" in server.handlers
    assert server.handlers["math.square"](4) == {"squared": 16}
