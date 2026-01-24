"""Projects RPC handlers."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from devflow.core.config import load_project_config


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

        # Enrich with current status
        enriched = []
        for project in projects:
            path = Path(project.get("path", ""))
            has_config = (path / "devflow.yml").exists() if path.exists() else False

            enriched.append(
                {
                    **project,
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

        # Add new project
        new_project = {
            "name": name,
            "path": str(project_path),
            "configured_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
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
