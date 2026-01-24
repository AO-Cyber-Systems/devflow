"""Development environment RPC handlers."""

from pathlib import Path
from typing import Any

from devflow.core.config import load_project_config
from devflow.providers.docker import DockerProvider


class DevHandler:
    """Handler for development environment RPC methods."""

    def __init__(self) -> None:
        self._docker = DockerProvider()

    def status(self, path: str) -> dict[str, Any]:
        """Get development environment status."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"error": "No devflow.yml configuration found"}

            if not config.development:
                return {"error": "No development configuration found"}

            # Get container statuses
            services = []
            compose_file = project_path / config.development.compose_file

            if compose_file.exists():
                # Get running containers
                containers = self._docker.compose_ps(
                    compose_file=str(compose_file), project_dir=str(project_path)
                )

                for container in containers:
                    services.append(
                        {
                            "name": container.get("Service", "unknown"),
                            "image": container.get("Image", ""),
                            "status": container.get("State", "unknown"),
                            "ports": container.get("Ports", []),
                            "health": container.get("Health"),
                        }
                    )

            return {
                "project": config.project.name,
                "services": services,
                "infrastructure_connected": config.infrastructure.enabled
                if config.infrastructure
                else False,
            }
        except Exception as e:
            return {"error": str(e)}

    def start(
        self, path: str, service: str | None = None, detach: bool = True
    ) -> dict[str, Any]:
        """Start development environment."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.development:
                return {"success": False, "error": "No development configuration found"}

            compose_file = project_path / config.development.compose_file
            if not compose_file.exists():
                return {
                    "success": False,
                    "error": f"Compose file not found: {compose_file}",
                }

            # Start services
            services_to_start = [service] if service else config.development.services
            success = self._docker.compose_up(
                compose_file=str(compose_file),
                project_dir=str(project_path),
                services=services_to_start if services_to_start else None,
                detach=detach,
            )

            return {
                "success": success,
                "message": "Services started" if success else "Failed to start services",
                "services_affected": services_to_start or [],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop(self, path: str, service: str | None = None) -> dict[str, Any]:
        """Stop development environment."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.development:
                return {"success": False, "error": "No development configuration found"}

            compose_file = project_path / config.development.compose_file

            services_to_stop = [service] if service else None
            success = self._docker.compose_down(
                compose_file=str(compose_file),
                project_dir=str(project_path),
                services=services_to_stop,
            )

            return {
                "success": success,
                "message": "Services stopped" if success else "Failed to stop services",
                "services_affected": services_to_stop or config.development.services,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restart(self, path: str, service: str) -> dict[str, Any]:
        """Restart a development service."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.development:
                return {"success": False, "error": "No development configuration found"}

            compose_file = project_path / config.development.compose_file

            success = self._docker.compose_restart(
                compose_file=str(compose_file),
                project_dir=str(project_path),
                services=[service],
            )

            return {
                "success": success,
                "message": f"Service {service} restarted"
                if success
                else f"Failed to restart {service}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def logs(
        self,
        path: str,
        service: str,
        tail: int | None = None,
        follow: bool = False,
        since: str | None = None,
    ) -> dict[str, Any]:
        """Get service logs.

        Args:
            path: Project path
            service: Service name
            tail: Number of lines to return
            follow: Follow log output (not recommended for RPC)
            since: Show logs since timestamp (e.g., "2021-01-01T00:00:00Z" or "10m")

        Returns:
            Dict with log output and last_timestamp for polling
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"error": "No devflow.yml configuration found"}

            if not config.development:
                return {"error": "No development configuration found"}

            compose_file = project_path / config.development.compose_file

            logs = self._docker.compose_logs(
                compose_file=str(compose_file),
                project_dir=str(project_path),
                services=[service],
                tail=tail or 100,
                follow=follow,
                since=since,
            )

            # Extract last timestamp for polling
            last_timestamp = None
            log_lines = logs.strip().split("\n") if logs else []
            if log_lines:
                # Docker compose log format may vary
                # Try to extract timestamp from last line
                last_line = log_lines[-1]
                if last_line and "|" in last_line:
                    # Format: "service-1  | timestamp message"
                    parts = last_line.split("|", 1)
                    if len(parts) > 1:
                        msg = parts[1].strip()
                        # Check for ISO timestamp at start
                        if msg and "T" in msg[:30] and "Z" in msg[:30]:
                            ts_parts = msg.split(" ", 1)
                            if ts_parts:
                                last_timestamp = ts_parts[0]

            return {
                "service": service,
                "logs": logs,
                "last_timestamp": last_timestamp,
            }
        except Exception as e:
            return {"error": str(e)}

    def run_in_container(self, path: str, service: str, command: list[str]) -> dict[str, Any]:
        """Run command in container."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.development:
                return {"success": False, "error": "No development configuration found"}

            compose_file = project_path / config.development.compose_file

            result = self._docker.compose_run(
                compose_file=str(compose_file),
                project_dir=str(project_path),
                service=service,
                command=command,
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reset(self, path: str, remove_volumes: bool = False) -> dict[str, Any]:
        """Reset development environment."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.development:
                return {"success": False, "error": "No development configuration found"}

            compose_file = project_path / config.development.compose_file

            success = self._docker.compose_down(
                compose_file=str(compose_file),
                project_dir=str(project_path),
                volumes=remove_volumes,
            )

            return {
                "success": success,
                "message": "Environment reset" if success else "Failed to reset",
                "volumes_removed": remove_volumes,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def setup(self, path: str) -> dict[str, Any]:
        """Run development setup."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            steps = []

            # Check compose file
            compose_file = project_path / (
                config.development.compose_file if config.development else "docker-compose.yml"
            )
            steps.append(
                {
                    "step": "Check compose file",
                    "status": "completed" if compose_file.exists() else "failed",
                    "message": str(compose_file) if compose_file.exists() else "Not found",
                }
            )

            # Pull images
            if compose_file.exists():
                steps.append(
                    {
                        "step": "Pull images",
                        "status": "pending",
                        "message": "Images would be pulled",
                    }
                )

            # Build images
            steps.append(
                {
                    "step": "Build images",
                    "status": "pending",
                    "message": "Images would be built",
                }
            )

            return {"success": True, "steps": steps}
        except Exception as e:
            return {"success": False, "error": str(e)}
