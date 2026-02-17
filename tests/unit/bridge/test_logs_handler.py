"""Tests for logs handler."""

from unittest.mock import MagicMock, patch

import pytest

from bridge.handlers.logs import LogsHandler


@pytest.fixture
def logs_handler() -> LogsHandler:
    """Create a LogsHandler for testing."""
    return LogsHandler()


@pytest.fixture
def mock_docker_available():
    """Mock Docker as available and authenticated."""
    with patch.object(LogsHandler, "_docker", create=True) as mock:
        mock_docker = MagicMock()
        mock_docker.is_available.return_value = True
        mock_docker.is_authenticated.return_value = True
        yield mock_docker


class TestLogsHandlerListContainers:
    """Tests for list_containers method."""

    def test_list_containers_success(self, logs_handler: LogsHandler) -> None:
        """Test listing containers successfully."""
        with patch.object(logs_handler, "_docker") as mock_docker:
            mock_docker.is_available.return_value = True
            mock_docker.is_authenticated.return_value = True
            mock_docker.run.return_value = MagicMock(
                stdout="abc123\ttraefik\tUp 2 hours\ttraefik:latest\ndef456\tnginx\tUp 1 hour\tnginx:alpine"
            )

            result = logs_handler.list_containers()

            assert result["success"] is True
            assert len(result["containers"]) == 2
            assert result["containers"][0]["id"] == "abc123"
            assert result["containers"][0]["name"] == "traefik"
            assert result["containers"][0]["status"] == "Up 2 hours"
            assert result["containers"][0]["image"] == "traefik:latest"
            assert result["containers"][1]["name"] == "nginx"

    def test_list_containers_docker_unavailable(self, logs_handler: LogsHandler) -> None:
        """Test listing containers when Docker is unavailable."""
        with patch.object(logs_handler, "_docker") as mock_docker:
            mock_docker.is_available.return_value = False

            result = logs_handler.list_containers()

            assert result["success"] is False
            assert result["containers"] == []
            assert "Docker not available" in result["error"]

    def test_list_containers_docker_not_authenticated(self, logs_handler: LogsHandler) -> None:
        """Test listing containers when Docker is not authenticated."""
        with patch.object(logs_handler, "_docker") as mock_docker:
            mock_docker.is_available.return_value = True
            mock_docker.is_authenticated.return_value = False

            result = logs_handler.list_containers()

            assert result["success"] is False
            assert "Docker not available" in result["error"]

    def test_list_containers_empty(self, logs_handler: LogsHandler) -> None:
        """Test listing when no containers are running."""
        with patch.object(logs_handler, "_docker") as mock_docker:
            mock_docker.is_available.return_value = True
            mock_docker.is_authenticated.return_value = True
            mock_docker.run.return_value = MagicMock(stdout="")

            result = logs_handler.list_containers()

            assert result["success"] is True
            assert result["containers"] == []

    def test_list_containers_exception(self, logs_handler: LogsHandler) -> None:
        """Test listing containers when an exception occurs."""
        with patch.object(logs_handler, "_docker") as mock_docker:
            mock_docker.is_available.return_value = True
            mock_docker.is_authenticated.return_value = True
            mock_docker.run.side_effect = Exception("Docker error")

            result = logs_handler.list_containers()

            assert result["success"] is False
            assert "Docker error" in result["error"]


class TestLogsHandlerGetLogs:
    """Tests for get_logs method."""

    def test_get_logs_success(self, logs_handler: LogsHandler) -> None:
        """Test getting logs successfully."""
        log_output = """2024-01-15T10:30:45.123456Z Starting server...
2024-01-15T10:30:46.789012Z Server listening on port 80
2024-01-15T10:30:47.456789Z Received request"""

        with patch.object(logs_handler, "_docker") as mock_docker:
            mock_docker.is_available.return_value = True
            mock_docker.is_authenticated.return_value = True
            mock_docker.run.return_value = MagicMock(stdout=log_output, stderr="")

            result = logs_handler.get_logs("traefik", lines=50)

            assert "error" not in result
            assert result["container"] == "traefik"
            assert result["count"] == 3
            assert len(result["logs"]) == 3
            assert result["logs"][0]["message"] == "Starting server..."
            assert result["logs"][0]["timestamp"] is not None

    def test_get_logs_with_timestamps(self, logs_handler: LogsHandler) -> None:
        """Test getting logs with timestamps enabled."""
        with patch.object(logs_handler, "_docker") as mock_docker:
            mock_docker.is_available.return_value = True
            mock_docker.is_authenticated.return_value = True
            mock_docker.run.return_value = MagicMock(stdout="", stderr="")

            logs_handler.get_logs("test", timestamps=True)

            call_args = mock_docker.run.call_args[0][0]
            assert "--timestamps" in call_args

    def test_get_logs_with_since(self, logs_handler: LogsHandler) -> None:
        """Test getting logs with since parameter."""
        with patch.object(logs_handler, "_docker") as mock_docker:
            mock_docker.is_available.return_value = True
            mock_docker.is_authenticated.return_value = True
            mock_docker.run.return_value = MagicMock(stdout="", stderr="")

            logs_handler.get_logs("test", since="1h")

            call_args = mock_docker.run.call_args[0][0]
            assert "--since" in call_args
            assert "1h" in call_args

    def test_get_logs_docker_unavailable(self, logs_handler: LogsHandler) -> None:
        """Test getting logs when Docker is unavailable."""
        with patch.object(logs_handler, "_docker") as mock_docker:
            mock_docker.is_available.return_value = False

            result = logs_handler.get_logs("traefik")

            assert result["logs"] == []
            assert "Docker not available" in result["error"]

    def test_get_logs_exception(self, logs_handler: LogsHandler) -> None:
        """Test getting logs when an exception occurs."""
        with patch.object(logs_handler, "_docker") as mock_docker:
            mock_docker.is_available.return_value = True
            mock_docker.is_authenticated.return_value = True
            mock_docker.run.side_effect = Exception("Container not found")

            result = logs_handler.get_logs("nonexistent")

            assert result["logs"] == []
            assert result["container"] == "nonexistent"
            assert "Container not found" in result["error"]


class TestLogsHandlerGetTraefikLogs:
    """Tests for get_traefik_logs method."""

    def test_get_traefik_logs_first_name(self, logs_handler: LogsHandler) -> None:
        """Test getting Traefik logs with first container name."""
        with patch.object(logs_handler, "get_logs") as mock_get_logs:
            mock_get_logs.return_value = {
                "logs": [{"message": "test", "level": "info"}],
                "container": "traefik",
                "count": 1,
            }

            result = logs_handler.get_traefik_logs()

            mock_get_logs.assert_called_once_with("traefik", lines=100, since=None)
            assert result["logs"][0]["message"] == "test"

    def test_get_traefik_logs_fallback_name(self, logs_handler: LogsHandler) -> None:
        """Test getting Traefik logs falls back to alternative names."""
        call_count = [0]

        def mock_get_logs_side_effect(container, **kwargs):
            call_count[0] += 1
            if container == "traefik":
                return {"logs": [], "error": "Container not found"}
            elif container == "devflow_traefik":
                return {
                    "logs": [{"message": "test"}],
                    "container": "devflow_traefik",
                    "count": 1,
                }
            return {"logs": [], "error": "Container not found"}

        with patch.object(logs_handler, "get_logs", side_effect=mock_get_logs_side_effect):
            result = logs_handler.get_traefik_logs()

            assert result["logs"][0]["message"] == "test"
            assert call_count[0] == 2  # Should have tried traefik first, then devflow_traefik

    def test_get_traefik_logs_not_found(self, logs_handler: LogsHandler) -> None:
        """Test getting Traefik logs when no Traefik container exists."""
        with patch.object(logs_handler, "get_logs") as mock_get_logs:
            mock_get_logs.return_value = {"logs": [], "error": "Container not found"}

            result = logs_handler.get_traefik_logs()

            assert result["logs"] == []
            assert "Traefik container not found" in result["error"]


class TestLogsHandlerParseLogs:
    """Tests for _parse_logs method."""

    def test_parse_logs_with_timestamps(self, logs_handler: LogsHandler) -> None:
        """Test parsing logs with Docker timestamps."""
        output = """2024-01-15T10:30:45.123456789Z Starting application
2024-01-15T10:30:46.987654321Z Application ready"""

        result = logs_handler._parse_logs(output, "test")

        assert len(result) == 2
        assert result[0]["timestamp"] is not None
        assert result[0]["message"] == "Starting application"
        assert result[0]["source"] == "test"
        assert result[1]["message"] == "Application ready"

    def test_parse_logs_without_timestamps(self, logs_handler: LogsHandler) -> None:
        """Test parsing logs without timestamps."""
        output = """Starting application
Application ready"""

        result = logs_handler._parse_logs(output, "test")

        assert len(result) == 2
        assert result[0]["timestamp"] is None
        assert result[0]["message"] == "Starting application"

    def test_parse_logs_empty(self, logs_handler: LogsHandler) -> None:
        """Test parsing empty log output."""
        result = logs_handler._parse_logs("", "test")
        assert result == []

    def test_parse_logs_with_blank_lines(self, logs_handler: LogsHandler) -> None:
        """Test parsing logs with blank lines."""
        output = """Line 1

Line 2

"""
        result = logs_handler._parse_logs(output, "test")
        assert len(result) == 2


class TestLogsHandlerDetectLevel:
    """Tests for _detect_level method."""

    def test_detect_level_error(self, logs_handler: LogsHandler) -> None:
        """Test detecting error level."""
        assert logs_handler._detect_level("ERROR: Something went wrong") == "error"
        assert logs_handler._detect_level("fatal error occurred") == "error"
        assert logs_handler._detect_level("panic: runtime error") == "error"
        assert logs_handler._detect_level("Exception raised") == "error"

    def test_detect_level_warning(self, logs_handler: LogsHandler) -> None:
        """Test detecting warning level."""
        assert logs_handler._detect_level("WARNING: Deprecated API") == "warning"
        assert logs_handler._detect_level("warn: resource low") == "warning"

    def test_detect_level_debug(self, logs_handler: LogsHandler) -> None:
        """Test detecting debug level."""
        assert logs_handler._detect_level("DEBUG: variable=value") == "debug"
        assert logs_handler._detect_level("trace: entering function") == "debug"
        assert logs_handler._detect_level("verbose output") == "debug"

    def test_detect_level_info(self, logs_handler: LogsHandler) -> None:
        """Test detecting info level (default)."""
        assert logs_handler._detect_level("Server started") == "info"
        assert logs_handler._detect_level("Request processed") == "info"
        assert logs_handler._detect_level("INFO: Application ready") == "info"


class TestLogsHandlerGetServiceLogs:
    """Tests for get_service_logs method."""

    def test_get_service_logs_success(self, logs_handler: LogsHandler) -> None:
        """Test getting service logs successfully."""
        with patch.object(logs_handler, "_docker") as mock_docker:
            mock_docker.is_available.return_value = True
            mock_docker.is_authenticated.return_value = True
            mock_docker.service_logs_text.return_value = "2024-01-15T10:30:45.123Z Service started"

            result = logs_handler.get_service_logs("my-service", lines=50)

            assert "error" not in result
            assert result["service"] == "my-service"
            assert result["count"] == 1
            mock_docker.service_logs_text.assert_called_once_with(
                "my-service", tail=50, since=None
            )

    def test_get_service_logs_docker_unavailable(self, logs_handler: LogsHandler) -> None:
        """Test getting service logs when Docker is unavailable."""
        with patch.object(logs_handler, "_docker") as mock_docker:
            mock_docker.is_available.return_value = False

            result = logs_handler.get_service_logs("my-service")

            assert result["logs"] == []
            assert "Docker not available" in result["error"]
