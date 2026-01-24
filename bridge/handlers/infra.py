"""Infrastructure RPC handlers."""

from pathlib import Path
from typing import Any

from devflow.core.config import load_project_config, load_global_config, InfrastructureConfig
from devflow.providers.infrastructure import InfrastructureProvider


class InfraHandler:
    """Handler for infrastructure RPC methods."""

    def __init__(self) -> None:
        self._provider: InfrastructureProvider | None = None

    def _get_provider(self) -> InfrastructureProvider:
        """Get or create infrastructure provider."""
        if self._provider is None:
            try:
                global_config = load_global_config()
                # Create InfrastructureConfig from global settings
                # GlobalInfrastructureConfig has different fields than InfrastructureConfig
                infra_config = InfrastructureConfig(
                    enabled=True,  # Assume enabled when accessing via UI
                    network_name=global_config.defaults.network_name or "devflow-proxy",
                )
                self._provider = InfrastructureProvider(infra_config)
            except Exception:
                # Use default config if global config not found
                self._provider = InfrastructureProvider(None)
        return self._provider

    def status(self) -> dict[str, Any]:
        """Get infrastructure status."""
        try:
            provider = self._get_provider()
            status = provider.status()
            return status.to_dict()
        except Exception as e:
            return {"error": str(e)}

    def start(self, force_recreate: bool = False) -> dict[str, Any]:
        """Start infrastructure (Traefik, network)."""
        try:
            provider = self._get_provider()
            result = provider.start(force_recreate=force_recreate)
            return {
                "success": result.success,
                "message": result.message,
                "details": result.details,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop(self, remove_volumes: bool = False, remove_network: bool = False) -> dict[str, Any]:
        """Stop infrastructure."""
        try:
            provider = self._get_provider()
            result = provider.stop(remove_volumes=remove_volumes, remove_network=remove_network)
            return {
                "success": result.success,
                "message": result.message,
                "details": result.details,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def configure(self, path: str, compose_file: str | None = None, dry_run: bool = False) -> dict[str, Any]:
        """Configure a project for infrastructure."""
        try:
            project_path = Path(path).resolve()
            if not project_path.exists():
                return {"success": False, "error": f"Path does not exist: {path}"}

            # Load project config
            config = load_project_config(project_path)
            provider = self._get_provider()

            # Get compose file
            if compose_file is None:
                compose_file = config.development.compose_file if config.development else "docker-compose.yml"

            compose_path = project_path / compose_file
            if not compose_path.exists():
                return {
                    "success": False,
                    "error": f"Compose file not found: {compose_path}",
                }

            # Configure project
            result = provider.configure_project(
                project_name=config.project.name,
                project_path=project_path,
                compose_file=compose_path,
                dry_run=dry_run,
            )

            return {
                "success": result.success,
                "message": result.message,
                "details": result.details,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def unconfigure(self, path: str) -> dict[str, Any]:
        """Remove a project from infrastructure configuration."""
        try:
            project_path = Path(path).resolve()
            provider = self._get_provider()

            result = provider.unconfigure_project(project_path)
            return {
                "success": result.success,
                "message": result.message,
                "details": result.details,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def regenerate_certs(self, domains: list[str] | None = None) -> dict[str, Any]:
        """Regenerate TLS certificates."""
        try:
            provider = self._get_provider()
            result = provider.regenerate_certificates(domains=domains)
            return {
                "success": result.success,
                "message": result.message,
                "details": result.details,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def hosts(self, action: str, domains: list[str] | None = None) -> dict[str, Any]:
        """Manage hosts file entries."""
        try:
            provider = self._get_provider()

            if action == "add" and domains:
                result = provider.add_hosts_entries(domains)
            elif action == "remove" and domains:
                result = provider.remove_hosts_entries(domains)
            elif action == "list":
                entries = provider.get_hosts_entries()
                return {"success": True, "entries": entries}
            else:
                return {"success": False, "error": f"Invalid action: {action}"}

            return {
                "success": result.success,
                "message": result.message,
                "details": result.details,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def doctor(self) -> dict[str, Any]:
        """Run infrastructure diagnostics."""
        try:
            provider = self._get_provider()
            return provider.doctor()
        except Exception as e:
            return {"error": str(e)}

    def registered_projects(self) -> dict[str, Any]:
        """Get list of projects registered with infrastructure."""
        try:
            provider = self._get_provider()
            projects = provider.get_registered_projects()
            return {
                "projects": [
                    {
                        "name": p.name,
                        "path": str(p.path),
                        "domains": p.domains,
                        "compose_files": [str(f) for f in p.compose_files],
                        "configured_at": p.configured_at,
                    }
                    for p in projects
                ],
                "total": len(projects),
            }
        except Exception as e:
            return {"error": str(e)}
