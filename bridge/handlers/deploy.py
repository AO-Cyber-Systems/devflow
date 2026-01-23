"""Deployment RPC handlers."""

from pathlib import Path
from typing import Any

from devflow.core.config import load_project_config
from devflow.providers.docker import DockerProvider
from devflow.providers.ssh import SSHProvider


class DeployHandler:
    """Handler for deployment RPC methods."""

    def __init__(self) -> None:
        self._docker = DockerProvider()

    def status(
        self, path: str, environment: str, service: str | None = None
    ) -> dict[str, Any]:
        """Get deployment status."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config.deployment:
                return {"error": "No deployment configuration found"}

            env_config = config.deployment.environments.get(environment)
            if not env_config:
                return {"error": f"Environment not found: {environment}"}

            # Get services status
            services = []
            services_config = config.deployment.services

            if service:
                if service in services_config:
                    services_config = {service: services_config[service]}
                else:
                    return {"error": f"Service not found: {service}"}

            for svc_name, svc_config in services_config.items():
                services.append(
                    {
                        "name": svc_name,
                        "image": svc_config.image,
                        "replicas": f"?/{svc_config.replicas}",
                        "status": "unknown",
                        "last_updated": None,
                    }
                )

            return {
                "environment": environment,
                "host": env_config.host,
                "services": services,
                "last_deploy": None,
            }
        except Exception as e:
            return {"error": str(e)}

    def deploy(
        self,
        path: str,
        environment: str,
        service: str | None = None,
        migrate: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Deploy to environment."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config.deployment:
                return {"success": False, "error": "No deployment configuration found"}

            env_config = config.deployment.environments.get(environment)
            if not env_config:
                return {"success": False, "error": f"Environment not found: {environment}"}

            # Check if production and needs confirmation
            if environment == "production" and env_config.require_approval and not dry_run:
                return {
                    "success": False,
                    "error": "Production deployment requires approval",
                    "requires_approval": True,
                }

            # Get services to deploy
            services_to_deploy = config.deployment.services
            if service:
                if service in services_to_deploy:
                    services_to_deploy = {service: services_to_deploy[service]}
                else:
                    return {"success": False, "error": f"Service not found: {service}"}

            results = []
            for svc_name, svc_config in services_to_deploy.items():
                results.append(
                    {
                        "service": svc_name,
                        "status": "would_deploy" if dry_run else "pending",
                        "image": svc_config.image,
                        "error": None,
                    }
                )

            return {
                "success": True,
                "deployed": 0 if dry_run else len(results),
                "failed": 0,
                "dry_run": dry_run,
                "results": results,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def rollback(
        self, path: str, environment: str, service: str | None = None
    ) -> dict[str, Any]:
        """Rollback deployment."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config.deployment:
                return {"success": False, "error": "No deployment configuration found"}

            env_config = config.deployment.environments.get(environment)
            if not env_config:
                return {"success": False, "error": f"Environment not found: {environment}"}

            # Get services to rollback
            services_to_rollback = config.deployment.services
            if service:
                if service in services_to_rollback:
                    services_to_rollback = {service: services_to_rollback[service]}
                else:
                    return {"success": False, "error": f"Service not found: {service}"}

            results = []
            for svc_name in services_to_rollback:
                results.append(
                    {
                        "service": svc_name,
                        "status": "pending",
                        "error": None,
                    }
                )

            return {
                "success": True,
                "rolled_back": 0,
                "failed": 0,
                "results": results,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def logs(
        self,
        path: str,
        environment: str,
        service: str,
        tail: int | None = None,
        follow: bool = False,
    ) -> dict[str, Any]:
        """Get deployment logs."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config.deployment:
                return {"error": "No deployment configuration found"}

            env_config = config.deployment.environments.get(environment)
            if not env_config:
                return {"error": f"Environment not found: {environment}"}

            # Get logs from remote
            # This is a simplified version
            return {
                "service": service,
                "environment": environment,
                "logs": "Log streaming not implemented in bridge",
            }
        except Exception as e:
            return {"error": str(e)}

    def ssh_command(
        self, path: str, environment: str, node: str | None = None
    ) -> dict[str, Any]:
        """Get SSH command for environment."""
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config.deployment:
                return {"error": "No deployment configuration found"}

            env_config = config.deployment.environments.get(environment)
            if not env_config:
                return {"error": f"Environment not found: {environment}"}

            if not env_config.host:
                return {"error": "No host configured for environment"}

            ssh_user = env_config.ssh_user or "deploy"
            host = node or env_config.host

            return {
                "command": f"ssh {ssh_user}@{host}",
                "user": ssh_user,
                "host": host,
            }
        except Exception as e:
            return {"error": str(e)}
