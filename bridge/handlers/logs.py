"""Logs RPC handlers - container log streaming and viewing."""

import re
from typing import Any

from devflow.providers.docker import DockerProvider


class LogsHandler:
    """Handler for log-related RPC methods."""

    def __init__(self) -> None:
        self._docker = DockerProvider()

    def list_containers(self) -> dict[str, Any]:
        """List all running containers available for log viewing.

        Returns:
            Dict with containers list containing name, id, status, and image.
        """
        if not self._docker.is_available() or not self._docker.is_authenticated():
            return {"success": False, "containers": [], "error": "Docker not available"}

        try:
            result = self._docker.run(["ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}"])
            containers = []

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 4:
                    containers.append({
                        "id": parts[0],
                        "name": parts[1],
                        "status": parts[2],
                        "image": parts[3],
                    })

            return {"success": True, "containers": containers}
        except Exception as e:
            return {"success": False, "containers": [], "error": str(e)}

    def get_logs(
        self,
        container: str,
        lines: int = 100,
        since: str | None = None,
        timestamps: bool = True,
    ) -> dict[str, Any]:
        """Get logs from a specific container.

        Args:
            container: Container name or ID
            lines: Number of lines to retrieve (tail)
            since: Show logs since timestamp (e.g., "10m", "1h", "2024-01-01T00:00:00Z")
            timestamps: Include timestamps in output

        Returns:
            Dict with logs array and container info.
        """
        if not self._docker.is_available() or not self._docker.is_authenticated():
            return {"logs": [], "error": "Docker not available"}

        try:
            args = ["logs", f"--tail={lines}"]
            if timestamps:
                args.append("--timestamps")
            if since:
                args.extend(["--since", since])
            args.append(container)

            result = self._docker.run(args, timeout=30)
            output = result.stdout + result.stderr  # Docker logs go to stderr

            log_entries = self._parse_logs(output, container)

            return {
                "logs": log_entries,
                "container": container,
                "count": len(log_entries),
            }
        except Exception as e:
            return {"logs": [], "container": container, "error": str(e)}

    def get_service_logs(
        self,
        service: str,
        lines: int = 100,
        since: str | None = None,
    ) -> dict[str, Any]:
        """Get logs from a Docker Swarm service.

        Args:
            service: Service name
            lines: Number of lines to retrieve
            since: Show logs since timestamp

        Returns:
            Dict with logs array and service info.
        """
        if not self._docker.is_available() or not self._docker.is_authenticated():
            return {"logs": [], "error": "Docker not available"}

        try:
            logs_text = self._docker.service_logs_text(service, tail=lines, since=since)
            log_entries = self._parse_logs(logs_text, service)

            return {
                "logs": log_entries,
                "service": service,
                "count": len(log_entries),
            }
        except Exception as e:
            return {"logs": [], "service": service, "error": str(e)}

    def get_traefik_logs(self, lines: int = 100, since: str | None = None) -> dict[str, Any]:
        """Get logs from Traefik specifically.

        Args:
            lines: Number of lines to retrieve
            since: Show logs since timestamp

        Returns:
            Dict with Traefik logs.
        """
        # Try common Traefik container names
        traefik_names = ["traefik", "devflow_traefik", "devflow-traefik"]

        for name in traefik_names:
            result = self.get_logs(name, lines=lines, since=since)
            if "error" not in result or result.get("logs"):
                return result

        return {"logs": [], "error": "Traefik container not found"}

    def _parse_logs(self, output: str, source: str) -> list[dict[str, Any]]:
        """Parse log output into structured entries.

        Args:
            output: Raw log output
            source: Container or service name

        Returns:
            List of log entry dicts with timestamp, level, message, source.
        """
        entries = []
        # Docker timestamp format: 2024-01-15T10:30:45.123456789Z
        timestamp_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z?)\s+(.*)$")

        for line in output.strip().split("\n"):
            if not line:
                continue

            timestamp = None
            message = line
            level = "info"

            # Try to extract timestamp
            match = timestamp_pattern.match(line)
            if match:
                try:
                    ts_str = match.group(1)
                    # Truncate nanoseconds to microseconds for Python
                    if "." in ts_str:
                        parts = ts_str.split(".")
                        if len(parts[1]) > 7:  # More than 6 digits + Z
                            ts_str = f"{parts[0]}.{parts[1][:6]}Z"
                    timestamp = ts_str
                    message = match.group(2)
                except (ValueError, IndexError):
                    pass

            # Detect log level from message content
            level = self._detect_level(message)

            entries.append({
                "timestamp": timestamp,
                "message": message,
                "level": level,
                "source": source,
            })

        return entries

    def _detect_level(self, message: str) -> str:
        """Detect log level from message content.

        Args:
            message: Log message

        Returns:
            Log level: debug, info, warning, or error.
        """
        message_lower = message.lower()

        if any(x in message_lower for x in ["error", "err", "fatal", "panic", "exception"]):
            return "error"
        elif any(x in message_lower for x in ["warn", "warning"]):
            return "warning"
        elif any(x in message_lower for x in ["debug", "trace", "verbose"]):
            return "debug"
        else:
            return "info"
