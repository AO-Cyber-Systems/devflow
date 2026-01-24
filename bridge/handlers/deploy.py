"""Deployment RPC handlers."""

import json
from pathlib import Path
from typing import Any

from devflow.core.config import load_project_config
from devflow.providers.docker import DockerProvider
from devflow.providers.ssh import SSHProvider


class DeployHandler:
    """Handler for deployment RPC methods."""

    def __init__(self) -> None:
        self._docker = DockerProvider()
        self._ssh = SSHProvider()

    def _build_service_name(self, stack: str, service: str) -> str:
        """Build the full Docker Swarm service name.

        Args:
            stack: Stack name from config
            service: Service name

        Returns:
            Full service name in format stack_service
        """
        return f"{stack}_{service}"

    def _build_image_tag(self, registry: str | None, org: str | None, image: str) -> str:
        """Build full image tag.

        Args:
            registry: Container registry (e.g., ghcr.io)
            org: Organization/namespace
            image: Image name with optional tag

        Returns:
            Full image tag
        """
        parts = []
        if registry:
            parts.append(registry)
        if org:
            parts.append(org)
        parts.append(image)
        return "/".join(parts)

    def _parse_service_json(self, json_output: str) -> list[dict]:
        """Parse Docker service JSON output.

        Args:
            json_output: JSON output from docker service ls

        Returns:
            List of service dicts
        """
        services = []
        for line in json_output.strip().split("\n"):
            if line:
                try:
                    services.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return services

    def status(self, path: str, environment: str, service: str | None = None) -> dict[str, Any]:
        """Get deployment status.

        Args:
            path: Project path
            environment: Target environment
            service: Optional specific service to check

        Returns:
            Dict with service status information
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"error": "No devflow.yml configuration found"}

            if not config.deployment:
                return {"error": "No deployment configuration found"}

            env_config = config.deployment.environments.get(environment)
            if not env_config:
                return {"error": f"Environment not found: {environment}"}

            # Get services config
            services_config = config.deployment.services
            if service:
                if service in services_config:
                    services_config = {service: services_config[service]}
                else:
                    return {"error": f"Service not found: {service}"}

            services = []

            for svc_name, svc_config in services_config.items():
                full_name = self._build_service_name(svc_config.stack, svc_name)
                svc_status = {
                    "name": svc_name,
                    "full_name": full_name,
                    "image": svc_config.image,
                    "expected_replicas": svc_config.replicas,
                    "replicas": "?",
                    "status": "unknown",
                    "last_updated": None,
                }

                if env_config.host:
                    # Remote: SSH execute docker service ls
                    ssh_user = env_config.ssh_user or "deploy"
                    cmd = f'docker service ls --filter "name={full_name}" --format "{{{{json .}}}}"'
                    result = self._ssh.execute(env_config.host, ssh_user, cmd)

                    if result.success and result.stdout.strip():
                        remote_services = self._parse_service_json(result.stdout)
                        for remote_svc in remote_services:
                            if remote_svc.get("Name") == full_name:
                                svc_status["replicas"] = remote_svc.get("Replicas", "?")
                                mode = remote_svc.get("Mode", "")
                                if "replicated" in mode.lower():
                                    svc_status["status"] = "running"
                                else:
                                    svc_status["status"] = mode or "unknown"
                                break
                else:
                    # Local: Docker provider
                    local_services = self._docker.list_services(filter_name=full_name)
                    for local_svc in local_services:
                        if local_svc.get("Name") == full_name:
                            svc_status["replicas"] = local_svc.get("Replicas", "?")
                            mode = local_svc.get("Mode", "")
                            if "replicated" in mode.lower():
                                svc_status["status"] = "running"
                            else:
                                svc_status["status"] = mode or "unknown"
                            break

                services.append(svc_status)

            return {
                "environment": environment,
                "host": env_config.host,
                "services": services,
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
        """Deploy to environment.

        Args:
            path: Project path
            environment: Target environment
            service: Optional specific service to deploy
            migrate: Run migrations before deploy
            dry_run: If True, only show what would be deployed

        Returns:
            Dict with deployment results
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

            if not config.deployment:
                return {"success": False, "error": "No deployment configuration found"}

            env_config = config.deployment.environments.get(environment)
            if not env_config:
                return {"success": False, "error": f"Environment not found: {environment}"}

            # Check if production and needs approval (should go through CI/CD)
            if env_config.require_approval and not dry_run:
                return {
                    "success": False,
                    "error": "This environment requires approval. Use CI/CD pipeline for deployments.",
                    "requires_approval": True,
                    "approval_environment": env_config.approval_environment,
                }

            # Get services to deploy
            services_to_deploy = config.deployment.services
            if service:
                if service in services_to_deploy:
                    services_to_deploy = {service: services_to_deploy[service]}
                else:
                    return {"success": False, "error": f"Service not found: {service}"}

            results = []
            deployed = 0
            failed = 0

            for svc_name, svc_config in services_to_deploy.items():
                full_name = self._build_service_name(svc_config.stack, svc_name)
                image_tag = self._build_image_tag(
                    config.deployment.registry,
                    config.deployment.organization,
                    svc_config.image,
                )

                result = {
                    "service": svc_name,
                    "full_name": full_name,
                    "image": image_tag,
                    "status": "would_deploy" if dry_run else "pending",
                    "error": None,
                }

                if dry_run:
                    results.append(result)
                    continue

                # Deploy the service
                if env_config.host:
                    # Remote: SSH execute docker service update
                    ssh_user = env_config.ssh_user or "deploy"
                    cmd = f"docker service update --image {image_tag} --with-registry-auth {full_name}"
                    ssh_result = self._ssh.execute(env_config.host, ssh_user, cmd, timeout=120)

                    if ssh_result.success:
                        result["status"] = "deployed"
                        deployed += 1
                    else:
                        result["status"] = "failed"
                        result["error"] = ssh_result.stderr or "Deployment failed"
                        failed += 1
                else:
                    # Local: Docker provider
                    success = self._docker.service_update(
                        full_name,
                        image=image_tag,
                        with_registry_auth=True,
                    )

                    if success:
                        result["status"] = "deployed"
                        deployed += 1
                    else:
                        result["status"] = "failed"
                        result["error"] = "Service update failed"
                        failed += 1

                results.append(result)

            return {
                "success": failed == 0,
                "deployed": deployed if not dry_run else 0,
                "failed": failed,
                "dry_run": dry_run,
                "results": results,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def rollback(self, path: str, environment: str, service: str | None = None) -> dict[str, Any]:
        """Rollback deployment.

        Args:
            path: Project path
            environment: Target environment
            service: Optional specific service to rollback

        Returns:
            Dict with rollback results
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"success": False, "error": "No devflow.yml configuration found"}

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
            rolled_back = 0
            failed = 0

            for svc_name, svc_config in services_to_rollback.items():
                full_name = self._build_service_name(svc_config.stack, svc_name)

                result = {
                    "service": svc_name,
                    "full_name": full_name,
                    "status": "pending",
                    "error": None,
                }

                if env_config.host:
                    # Remote: SSH execute docker service rollback
                    ssh_user = env_config.ssh_user or "deploy"
                    cmd = f"docker service rollback {full_name}"
                    ssh_result = self._ssh.execute(env_config.host, ssh_user, cmd, timeout=120)

                    if ssh_result.success:
                        result["status"] = "rolled_back"
                        rolled_back += 1
                    else:
                        result["status"] = "failed"
                        result["error"] = ssh_result.stderr or "Rollback failed"
                        failed += 1
                else:
                    # Local: Docker provider
                    success = self._docker.service_rollback(full_name)

                    if success:
                        result["status"] = "rolled_back"
                        rolled_back += 1
                    else:
                        result["status"] = "failed"
                        result["error"] = "Service rollback failed"
                        failed += 1

                results.append(result)

            return {
                "success": failed == 0,
                "rolled_back": rolled_back,
                "failed": failed,
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
        since: str | None = None,
    ) -> dict[str, Any]:
        """Get deployment logs.

        Args:
            path: Project path
            environment: Target environment
            service: Service name
            tail: Number of lines to return
            since: Show logs since timestamp (e.g., "2021-01-01T00:00:00Z" or "10m")

        Returns:
            Dict with log output
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"error": "No devflow.yml configuration found"}

            if not config.deployment:
                return {"error": "No deployment configuration found"}

            env_config = config.deployment.environments.get(environment)
            if not env_config:
                return {"error": f"Environment not found: {environment}"}

            svc_config = config.deployment.services.get(service)
            if not svc_config:
                return {"error": f"Service not found: {service}"}

            full_name = self._build_service_name(svc_config.stack, service)
            tail_count = tail or 100

            if env_config.host:
                # Remote: SSH execute docker service logs
                ssh_user = env_config.ssh_user or "deploy"
                cmd = f"docker service logs --tail {tail_count} --no-trunc {full_name}"
                if since:
                    cmd = f"docker service logs --tail {tail_count} --since {since} --no-trunc {full_name}"

                ssh_result = self._ssh.execute(env_config.host, ssh_user, cmd, timeout=30)

                if ssh_result.success:
                    logs = ssh_result.stdout
                else:
                    logs = ssh_result.stderr or "Failed to get logs"

            else:
                # Local: Docker provider
                logs = self._docker.service_logs_text(
                    full_name,
                    tail=tail_count,
                    since=since,
                )

            # Extract last timestamp for polling
            last_timestamp = None
            log_lines = logs.strip().split("\n") if logs else []
            if log_lines:
                # Docker log format typically starts with timestamp
                # e.g., "2024-01-15T10:30:00.123456789Z container_name | log message"
                last_line = log_lines[-1]
                if last_line and "Z" in last_line[:30]:
                    # Try to extract ISO timestamp
                    parts = last_line.split(" ", 1)
                    if parts and "T" in parts[0]:
                        last_timestamp = parts[0]

            return {
                "service": service,
                "full_name": full_name,
                "environment": environment,
                "logs": logs,
                "last_timestamp": last_timestamp,
            }
        except Exception as e:
            return {"error": str(e)}

    def ssh_command(self, path: str, environment: str, node: str | None = None) -> dict[str, Any]:
        """Get SSH command for environment.

        Args:
            path: Project path
            environment: Target environment
            node: Optional specific node to connect to

        Returns:
            Dict with SSH connection details
        """
        try:
            project_path = Path(path).resolve()
            config = load_project_config(project_path)

            if not config:
                return {"error": "No devflow.yml configuration found"}

            if not config.deployment:
                return {"error": "No deployment configuration found"}

            env_config = config.deployment.environments.get(environment)
            if not env_config:
                return {"error": f"Environment not found: {environment}"}

            if not env_config.host:
                return {"error": "No host configured for environment (local deployment)"}

            ssh_user = env_config.ssh_user or "deploy"
            host = node or env_config.host

            return {
                "command": f"ssh {ssh_user}@{host}",
                "user": ssh_user,
                "host": host,
            }
        except Exception as e:
            return {"error": str(e)}
