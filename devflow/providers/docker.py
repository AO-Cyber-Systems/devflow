"""Docker and Docker Swarm provider."""

import json
import shutil
import subprocess
from typing import Any, Optional

from devflow.providers.base import Provider


class DockerProvider(Provider):
    """Wrapper for Docker CLI."""

    @property
    def name(self) -> str:
        return "docker"

    @property
    def binary(self) -> str:
        return "docker"

    def is_available(self) -> bool:
        return shutil.which(self.binary) is not None

    def is_authenticated(self) -> bool:
        # For Docker, "authenticated" means the daemon is running
        if not self.is_available():
            return False

        try:
            result = subprocess.run(
                [self.binary, "info"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    # -------------------------------------------------------------------------
    # Docker Secrets
    # -------------------------------------------------------------------------

    def list_secrets(self) -> list[dict]:
        """List Docker secrets."""
        try:
            result = self.run(["secret", "ls", "--format", "json"])
            # Docker outputs one JSON object per line
            lines = result.stdout.strip().split("\n")
            return [json.loads(line) for line in lines if line]
        except subprocess.CalledProcessError:
            return []

    def create_secret(self, name: str, value: str) -> bool:
        """Create a Docker secret."""
        try:
            # Use stdin to avoid exposing secret
            result = subprocess.run(
                [self.binary, "secret", "create", name, "-"],
                input=value,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def remove_secret(self, name: str) -> bool:
        """Remove a Docker secret."""
        try:
            self.run(["secret", "rm", name])
            return True
        except subprocess.CalledProcessError:
            return False

    def secret_exists(self, name: str) -> bool:
        """Check if a secret exists."""
        secrets = self.list_secrets()
        return any(s.get("Name") == name for s in secrets)

    # -------------------------------------------------------------------------
    # Docker Services (Swarm)
    # -------------------------------------------------------------------------

    def list_services(self, filter_name: Optional[str] = None) -> list[dict]:
        """List Docker Swarm services."""
        args = ["service", "ls", "--format", "json"]
        if filter_name:
            args.extend(["--filter", f"name={filter_name}"])

        try:
            result = self.run(args)
            lines = result.stdout.strip().split("\n")
            return [json.loads(line) for line in lines if line]
        except subprocess.CalledProcessError:
            return []

    def service_update(
        self,
        service_name: str,
        image: Optional[str] = None,
        force: bool = False,
        with_registry_auth: bool = True,
    ) -> bool:
        """Update a Docker Swarm service."""
        args = ["service", "update"]

        if image:
            args.extend(["--image", image])
        if force:
            args.append("--force")
        if with_registry_auth:
            args.append("--with-registry-auth")

        args.append(service_name)

        try:
            self.run(args, timeout=120)
            return True
        except subprocess.CalledProcessError:
            return False

    def service_logs(
        self,
        service_name: str,
        tail: int = 100,
        follow: bool = False,
    ) -> subprocess.Popen:
        """Get logs from a service (returns a Popen for streaming)."""
        args = [self.binary, "service", "logs", f"--tail={tail}"]
        if follow:
            args.append("-f")
        args.append(service_name)

        return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    def service_rollback(self, service_name: str) -> bool:
        """Rollback a service to its previous version."""
        try:
            self.run(["service", "rollback", service_name])
            return True
        except subprocess.CalledProcessError:
            return False

    # -------------------------------------------------------------------------
    # Docker Stack (Swarm)
    # -------------------------------------------------------------------------

    def stack_deploy(self, stack_name: str, compose_file: str, with_registry_auth: bool = True) -> bool:
        """Deploy a Docker stack."""
        args = ["stack", "deploy", "-c", compose_file]
        if with_registry_auth:
            args.append("--with-registry-auth")
        args.append(stack_name)

        try:
            self.run(args, timeout=120)
            return True
        except subprocess.CalledProcessError:
            return False

    def stack_services(self, stack_name: str) -> list[dict]:
        """List services in a stack."""
        return self.list_services(filter_name=stack_name)

    # -------------------------------------------------------------------------
    # Docker Compose
    # -------------------------------------------------------------------------

    def compose_up(
        self,
        compose_file: str = "docker-compose.yml",
        detach: bool = True,
        services: Optional[list[str]] = None,
    ) -> bool:
        """Start services with docker compose."""
        args = ["compose", "-f", compose_file, "up"]
        if detach:
            args.append("-d")
        if services:
            args.extend(services)

        try:
            self.run(args, timeout=180)
            return True
        except subprocess.CalledProcessError:
            return False

    def compose_down(self, compose_file: str = "docker-compose.yml", volumes: bool = False) -> bool:
        """Stop services with docker compose."""
        args = ["compose", "-f", compose_file, "down"]
        if volumes:
            args.append("-v")

        try:
            self.run(args, timeout=60)
            return True
        except subprocess.CalledProcessError:
            return False
