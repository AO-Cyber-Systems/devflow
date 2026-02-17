"""Projects RPC handlers."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from devflow.core.config import load_project_config
from devflow.providers.docker import DockerProvider


class ProjectsHandler:
    """Handler for project management RPC methods."""

    def __init__(self) -> None:
        self._projects_file = Path.home() / ".devflow" / "projects.json"

    def _load_projects(self) -> list[dict[str, Any]]:
        """Load projects from file."""
        if not self._projects_file.exists():
            return []
        try:
            with open(self._projects_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_projects(self, projects: list[dict[str, Any]]) -> None:
        """Save projects to file."""
        self._projects_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._projects_file, "w") as f:
            json.dump(projects, f, indent=2)

    def list(self) -> dict[str, Any]:
        """List all registered projects."""
        projects = self._load_projects()

        # Enrich with current status and required fields for Swift UI
        enriched = []
        for project in projects:
            path = Path(project.get("path", ""))
            has_config = (path / "devflow.yml").exists() if path.exists() else False

            # Generate a stable ID from the path if not present
            project_id = project.get("id") or str(abs(hash(str(path))))

            enriched.append(
                {
                    "id": project_id,
                    "name": project.get("name", path.name),
                    "path": str(path),
                    "domain": project.get("domain"),
                    "port": project.get("port"),
                    "is_running": False,  # TODO: Check actual running status
                    "framework": project.get("framework"),
                    "last_accessed": project.get("last_accessed"),
                    "exists": path.exists(),
                    "has_devflow_config": has_config,
                }
            )

        return {"projects": enriched, "total": len(enriched)}

    def add(self, path: str) -> dict[str, Any]:
        """Add a project to the registry."""
        project_path = Path(path).resolve()

        if not project_path.exists():
            return {"error": f"Path does not exist: {path}"}

        if not project_path.is_dir():
            return {"error": f"Path is not a directory: {path}"}

        projects = self._load_projects()

        # Check if already registered
        for project in projects:
            if Path(project.get("path", "")).resolve() == project_path:
                return {"error": "Project already registered", "project": project}

        # Get project name from config or directory name
        name = project_path.name
        has_config = (project_path / "devflow.yml").exists()

        if has_config:
            try:
                config = load_project_config(project_path)
                name = config.project.name
            except Exception:
                pass

        # Generate a stable ID from the path
        project_id = str(abs(hash(str(project_path))))

        # Add new project with all required fields for Swift UI
        new_project = {
            "id": project_id,
            "name": name,
            "path": str(project_path),
            "domain": None,
            "port": None,
            "is_running": False,
            "framework": None,
            "last_accessed": datetime.now().isoformat(),
            "configured_at": datetime.now().isoformat(),
        }

        projects.append(new_project)
        self._save_projects(projects)

        return {"success": True, "project": new_project}

    def remove(self, path: str) -> dict[str, Any]:
        """Remove a project from the registry."""
        project_path = Path(path).resolve()
        projects = self._load_projects()

        # Find and remove project
        removed = None
        new_projects = []
        for project in projects:
            if Path(project.get("path", "")).resolve() == project_path:
                removed = project
            else:
                new_projects.append(project)

        if not removed:
            return {"error": "Project not found in registry"}

        self._save_projects(new_projects)
        return {"success": True, "removed": removed}

    def status(self, path: str) -> dict[str, Any]:
        """Get detailed status of a project."""
        project_path = Path(path).resolve()

        if not project_path.exists():
            return {"error": f"Path does not exist: {path}"}

        has_config = (project_path / "devflow.yml").exists()

        status = {
            "name": project_path.name,
            "path": str(project_path),
            "has_devflow_config": has_config,
            "infrastructure_enabled": False,
            "services_running": 0,
            "services_total": 0,
        }

        if has_config:
            try:
                config = load_project_config(project_path)
                status["name"] = config.project.name
                status["infrastructure_enabled"] = config.infrastructure.enabled if config.infrastructure else False

                if config.development:
                    status["services_total"] = len(config.development.services)

            except Exception as e:
                status["config_error"] = str(e)

        # Update last accessed
        projects = self._load_projects()
        for project in projects:
            if Path(project.get("path", "")).resolve() == project_path:
                project["last_accessed"] = datetime.now().isoformat()
                break
        self._save_projects(projects)

        return status

    def init(self, path: str, preset: str | None = None) -> dict[str, Any]:
        """Initialize a new project with devflow.yml."""
        project_path = Path(path).resolve()

        if not project_path.exists():
            return {"error": f"Path does not exist: {path}"}

        config_path = project_path / "devflow.yml"
        if config_path.exists():
            return {"error": "devflow.yml already exists"}

        # Load preset if specified
        preset_dir = Path(__file__).parent.parent.parent / "presets"
        template = None

        if preset:
            preset_file = preset_dir / f"{preset}.yml"
            if preset_file.exists():
                template = preset_file.read_text()
            else:
                return {"error": f"Preset not found: {preset}"}
        else:
            # Use default template
            template = f"""version: "1"

project:
  name: {project_path.name}

development:
  compose_file: docker-compose.yml
  services: []
  env: {{}}
  ports: {{}}

# Uncomment and configure as needed:
# database:
#   migrations:
#     directory: migrations
#     format: sql
#   environments:
#     local:
#       url_env: DATABASE_URL

# infrastructure:
#   enabled: false
#   network_name: devflow-proxy
"""

        # Write config file
        config_path.write_text(template)

        # Add to registry
        self.add(path)

        return {"success": True, "path": str(config_path), "preset": preset}

    def list_presets(self) -> dict[str, Any]:
        """List available project presets."""
        preset_dir = Path(__file__).parent.parent.parent / "presets"
        presets = []

        if preset_dir.exists():
            for preset_file in preset_dir.glob("*.yml"):
                presets.append({"name": preset_file.stem, "path": str(preset_file)})

        return {"presets": presets}

    def get_detail(self, path: str) -> dict[str, Any]:
        """Get detailed project info including services, ports, and volumes.

        Args:
            path: Path to the project directory.

        Returns:
            Dictionary with project details, services, ports, and volumes.
        """
        project_path = Path(path).resolve()

        if not project_path.exists():
            return {"error": f"Path does not exist: {path}"}

        # Get basic project info
        projects = self._load_projects()
        project_data = None
        for p in projects:
            if Path(p.get("path", "")).resolve() == project_path:
                project_data = p
                break

        if not project_data:
            project_data = {
                "id": str(hash(str(project_path))),
                "name": project_path.name,
                "path": str(project_path),
                "is_running": False,
            }

        # Find compose file
        compose_file = None
        for name in ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]:
            candidate = project_path / name
            if candidate.exists():
                compose_file = candidate
                break

        services = []
        ports = []
        volumes = []

        if compose_file:
            # Get services from docker compose
            services, ports, volumes = self._get_compose_info(project_path, compose_file)

            # Check if any service is running
            project_data["is_running"] = any(s.get("status", "").lower().startswith("up") for s in services)

        return {
            "project": project_data,
            "services": services,
            "ports": ports,
            "volumes": volumes,
            "has_compose_file": compose_file is not None,
            "compose_file_path": str(compose_file) if compose_file else None,
        }

    def _get_compose_info(
        self, project_path: Path, compose_file: Path
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """Get service info from docker compose.

        Returns:
            Tuple of (services, ports, volumes).
        """
        services = []
        ports = []
        volumes = []

        try:
            docker = DockerProvider()
            if not docker.is_available():
                return services, ports, volumes

            # Get running containers for this compose project
            result = docker.run(
                [
                    "compose",
                    "-f",
                    str(compose_file),
                    "ps",
                    "--format",
                    "json",
                ],
                cwd=str(project_path),
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                # Parse JSON output (docker compose ps --format json outputs one JSON per line)
                for line in result.stdout.strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        container = json.loads(line)
                        service_name = container.get("Service", container.get("Name", "unknown"))
                        service = {
                            "name": service_name,
                            "status": container.get("State", container.get("Status", "unknown")),
                            "image": container.get("Image", ""),
                            "container_id": container.get("ID", ""),
                            "ports": [],
                            "health": container.get("Health", None),
                        }

                        # Parse ports from Publishers or Ports field
                        publishers = container.get("Publishers") or []
                        for pub in publishers:
                            if isinstance(pub, dict) and pub.get("PublishedPort"):
                                port_info = {
                                    "service": service_name,
                                    "host_port": pub.get("PublishedPort", 0),
                                    "container_port": pub.get("TargetPort", 0),
                                    "host_ip": pub.get("URL", "0.0.0.0"),
                                }
                                ports.append(port_info)
                                service["ports"].append(
                                    f"{port_info['host_port']}:{port_info['container_port']}"
                                )

                        services.append(service)
                    except json.JSONDecodeError:
                        continue

            # Get volume info from compose config
            config_result = docker.run(
                ["compose", "-f", str(compose_file), "config", "--format", "json"],
                cwd=str(project_path),
                timeout=10,
            )

            if config_result.returncode == 0 and config_result.stdout.strip():
                try:
                    config = json.loads(config_result.stdout)
                    for svc_name, svc_config in config.get("services", {}).items():
                        for vol in svc_config.get("volumes", []):
                            if isinstance(vol, dict):
                                volumes.append({
                                    "service": svc_name,
                                    "host_path": vol.get("source", ""),
                                    "container_path": vol.get("target", ""),
                                    "mode": "ro" if vol.get("read_only") else "rw",
                                })
                            elif isinstance(vol, str) and ":" in vol:
                                parts = vol.split(":")
                                mode = "rw"
                                if len(parts) >= 3:
                                    mode = parts[2]
                                volumes.append({
                                    "service": svc_name,
                                    "host_path": parts[0],
                                    "container_path": parts[1] if len(parts) > 1 else "",
                                    "mode": mode,
                                })
                except json.JSONDecodeError:
                    pass

        except Exception:
            # Return empty if docker compose fails
            pass

        return services, ports, volumes
